"""Tests for the cleaning transformations in `src/cleaning.py`."""

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from src import cleaning


@pytest.fixture
def wide_wb():
    """Two indicators for two countries, in the raw World Bank wide shape."""
    return pd.DataFrame(
        {
            "Country Name": ["Portugal", "Portugal", "Brazil", "Brazil"],
            "Country Code": ["PRT", "PRT", "BRA", "BRA"],
            "Series Name": ["GDP", "Population", "GDP", "Population"],
            "Series Code": ["NY.GDP", "SP.POP", "NY.GDP", "SP.POP"],
            "2001 [YR2001]": ["1,000", "10", "2,000", "180"],
            "2002 [YR2002]": ["1,100", "..", "2,200", "182"],
        }
    )


class TestStandardiseCountryNames:
    """Country names must be aligned before the two sources can be merged."""

    def test_maps_names_present_in_the_mapping(self):
        df = pd.DataFrame({"Country Name": ["Korea, Rep.", "Czechia"]})

        result = cleaning.standardise_country_names(df, "Country Name")

        assert result["Country Name"].tolist() == [
            "South Korea",
            "Czech Republic",
        ]

    def test_leaves_unmapped_names_untouched(self):
        df = pd.DataFrame({"Country Name": ["Portugal", "Brazil"]})

        result = cleaning.standardise_country_names(df, "Country Name")

        assert result["Country Name"].tolist() == ["Portugal", "Brazil"]

    def test_does_not_mutate_the_input(self):
        df = pd.DataFrame({"Country Name": ["Korea, Rep."]})
        original = df.copy()

        cleaning.standardise_country_names(df, "Country Name")

        assert_frame_equal(df, original)


class TestDropUnmatchedCountries:
    """Junk rows and unmatched territories are removed, not silently kept."""

    def test_removes_only_the_listed_values(self):
        df = pd.DataFrame({"Country Name": ["Portugal", "Bermuda", "Brazil"]})

        result = cleaning.drop_unmatched_countries(
            df, "Country Name", ["Bermuda"]
        )

        assert result["Country Name"].tolist() == ["Portugal", "Brazil"]

    def test_the_shipped_list_catches_the_metadata_footer(self):
        assert (
            "Data from database: World Development Indicators"
            in cleaning.ROWS_TO_DROP
        )


class TestMeltYears:
    """The wide year columns become one row per country-indicator-year."""

    def test_produces_one_row_per_year_column(self, wide_wb):
        id_vars = [
            "Country Name",
            "Country Code",
            "Series Name",
            "Series Code",
        ]

        long = cleaning.melt_years(wide_wb, id_vars)

        assert len(long) == len(wide_wb) * 2

    def test_extracts_a_plain_integer_year(self, wide_wb):
        id_vars = [
            "Country Name",
            "Country Code",
            "Series Name",
            "Series Code",
        ]

        long = cleaning.melt_years(wide_wb, id_vars)

        assert long["Year"].dtype.kind == "i"
        assert sorted(long["Year"].unique()) == [2001, 2002]


class TestPivotIndicators:
    """Indicators become columns, leaving one row per country-year."""

    def test_gives_one_row_per_country_year(self, wide_wb):
        id_vars = [
            "Country Name",
            "Country Code",
            "Series Name",
            "Series Code",
        ]
        long = cleaning.melt_years(wide_wb, id_vars)

        wide = cleaning.pivot_indicators(
            long, ["Country Name", "Country Code", "Year"]
        )

        assert len(wide) == 4
        assert {"GDP", "Population"} <= set(wide.columns)

    def test_drops_the_columns_axis_name(self, wide_wb):
        id_vars = [
            "Country Name",
            "Country Code",
            "Series Name",
            "Series Code",
        ]
        long = cleaning.melt_years(wide_wb, id_vars)

        wide = cleaning.pivot_indicators(
            long, ["Country Name", "Country Code", "Year"]
        )

        assert wide.columns.name is None


class TestCodeToContinent:
    """ISO3 codes resolve to continents, with gaps instead of errors."""

    @pytest.mark.parametrize(
        ("code", "expected"),
        [
            ("PRT", "Europe"),
            ("BRA", "South America"),
            ("JPN", "Asia"),
            ("USA", "North America"),
            ("AUS", "Oceania"),
            ("NGA", "Africa"),
        ],
    )
    def test_resolves_known_codes(self, code, expected):
        assert cleaning.code_to_continent(code) == expected

    @pytest.mark.parametrize(
        ("code", "expected"), [("XKX", "Europe"), ("TLS", "Asia")]
    )
    def test_applies_the_overrides_pycountry_convert_cannot_resolve(
        self, code, expected
    ):
        assert cleaning.code_to_continent(code) == expected

    @pytest.mark.parametrize("code", ["ZZZ", None, float("nan"), 123])
    def test_returns_na_instead_of_raising(self, code):
        assert pd.isna(cleaning.code_to_continent(code))


class TestAddContinentColumn:
    """The continent column is derived per row from the ISO3 code."""

    def test_adds_a_continent_for_every_row(self):
        df = pd.DataFrame({"Country Code": ["PRT", "BRA", "ZZZ"]})

        result = cleaning.add_continent_column(df)

        assert result["Continent"].tolist()[:2] == ["Europe", "South America"]
        assert pd.isna(result["Continent"].iloc[2])

    def test_does_not_mutate_the_input(self):
        df = pd.DataFrame({"Country Code": ["PRT"]})

        cleaning.add_continent_column(df)

        assert "Continent" not in df.columns


class TestConvertColumnsToNumeric:
    """World Bank exports arrive as strings with separators and markers."""

    def test_strips_thousand_separators(self):
        df = pd.DataFrame({"GDP": ["1,000,000", "2,500"]})

        result = cleaning.convert_columns_to_numeric(df, ["GDP"])

        assert result["GDP"].tolist() == [1000000.0, 2500.0]

    def test_coerces_the_double_dot_null_marker_to_nan(self):
        df = pd.DataFrame({"GDP": ["1000", "..", "3000"]})

        result = cleaning.convert_columns_to_numeric(df, ["GDP"])

        assert result["GDP"].isna().tolist() == [False, True, False]

    def test_leaves_already_numeric_values_unchanged(self):
        df = pd.DataFrame({"GDP": [1000.5, 2000.25]})

        result = cleaning.convert_columns_to_numeric(df, ["GDP"])

        assert result["GDP"].tolist() == [1000.5, 2000.25]


class TestDecimalPlaces:
    """Spurious precision has to be visible before it can be removed."""

    def test_counts_the_stored_decimals_not_the_displayed_ones(self):
        df = pd.DataFrame({"Inflation": [3.6045218374651234, 1.5]})

        result = cleaning.decimal_places(df)

        assert result["Inflation"] == 16

    def test_ignores_trailing_zeros(self):
        df = pd.DataFrame({"GDP": [2813571754.0, 1000.0]})

        result = cleaning.decimal_places(df)

        assert result["GDP"] == 0

    def test_skips_non_numeric_columns(self):
        df = pd.DataFrame({"Country Name": ["Portugal"], "GDP": [1.25]})

        result = cleaning.decimal_places(df)

        assert result.index.tolist() == ["GDP"]

    def test_is_not_confused_by_missing_values(self):
        df = pd.DataFrame({"GDP": [1.25, None]})

        result = cleaning.decimal_places(df)

        assert result["GDP"] == 2


class TestRoundNumericColumns:
    """Every numeric column is pinned to the precision its source supports."""

    def test_rounds_each_column_to_its_mapped_precision(self):
        df = pd.DataFrame(
            {
                "GDP (current US$)": [2813571753.87253],
                "GDP growth (annual %)": [-9.431974328472],
                "Overall Score": [59.74],
            }
        )

        result = cleaning.round_numeric_columns(df)

        assert result["GDP (current US$)"].iloc[0] == 2813571754.0
        assert result["GDP growth (annual %)"].iloc[0] == -9.43
        assert result["Overall Score"].iloc[0] == 59.7

    def test_keeps_the_smallest_co2_readings_above_zero(self):
        col = (
            "Carbon dioxide (CO2) emissions (total) excluding LULUCF (Mt CO2e)"
        )
        df = pd.DataFrame({col: [0.0002]})

        result = cleaning.round_numeric_columns(df)

        assert result[col].iloc[0] == 0.0002

    def test_leaves_values_numeric_rather_than_formatted_strings(self):
        df = pd.DataFrame({"Overall Score": [59.74]})

        result = cleaning.round_numeric_columns(df)

        assert result["Overall Score"].dtype.kind == "f"

    def test_preserves_integer_columns_as_integers(self):
        df = pd.DataFrame({"Year": [2001], "Population, total": [20284307]})

        result = cleaning.round_numeric_columns(df)

        assert result["Year"].dtype.kind == "i"
        assert result["Population, total"].dtype.kind == "i"

    def test_preserves_missing_values(self):
        df = pd.DataFrame({"Overall Score": [59.74, None]})

        result = cleaning.round_numeric_columns(df)

        assert result["Overall Score"].isna().tolist() == [False, True]

    def test_ignores_non_numeric_columns(self):
        df = pd.DataFrame(
            {"Country Name": ["Portugal"], "Overall Score": [59.74]}
        )

        result = cleaning.round_numeric_columns(df)

        assert result["Country Name"].iloc[0] == "Portugal"

    def test_raises_for_a_numeric_column_with_no_mapped_precision(self):
        df = pd.DataFrame({"Some New Indicator": [1.23456789]})

        with pytest.raises(ValueError, match="Some New Indicator"):
            cleaning.round_numeric_columns(df)

    def test_does_not_mutate_the_input(self):
        df = pd.DataFrame({"GDP growth (annual %)": [-9.431974328472]})
        original = df.copy()

        cleaning.round_numeric_columns(df)

        assert_frame_equal(df, original)

    def test_the_shipped_mapping_covers_every_exported_column(self):
        exported = pd.read_csv("data/processed/wb_economic_freedom_merged.csv")

        numeric = exported.select_dtypes("number").columns

        assert set(numeric) <= set(cleaning.NUMERIC_PRECISION)


class TestCompareCountries:
    """The mismatch report drives the standardisation mapping."""

    def test_reports_the_symmetric_difference_of_both_columns(self):
        df1 = pd.DataFrame({"a": ["Portugal", "Brazil"]})
        df2 = pd.DataFrame({"b": ["Brazil", "Japan"]})

        only_1, only_2 = cleaning.compare_countries(df1, df2, "a", "b")

        assert only_1 == {"Portugal"}
        assert only_2 == {"Japan"}
