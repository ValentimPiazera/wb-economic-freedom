"""Tests for the coverage and panel helpers in `src/utils.py`."""

import pandas as pd
import pytest

from src import utils


@pytest.fixture
def panel():
    """Three countries built so between and within disagree in sign.

    Higher-scoring countries have higher outcomes on their long-run means,
    but inside every country the two move in opposite directions — the exact
    pattern a pooled correlation hides. The three slopes deliberately differ,
    because two countries moving identically cancel out under two-way
    demeaning and leave nothing to correlate.
    """
    return pd.DataFrame(
        {
            "Country Name": ["A"] * 4 + ["B"] * 4 + ["C"] * 4,
            "Year": [2001, 2002, 2003, 2004] * 3,
            "score": [
                10.0,
                20.0,
                30.0,
                40.0,
                40.0,
                45.0,
                50.0,
                55.0,
                70.0,
                72.0,
                74.0,
                76.0,
            ],
            "outcome": [
                4.0,
                3.0,
                2.0,
                1.0,
                7.0,
                6.5,
                6.0,
                5.5,
                9.0,
                8.0,
                7.0,
                6.0,
            ],
        }
    )


@pytest.fixture
def coverage_frame():
    """Three years: `full` is always complete, `late` only reports in 2023."""
    return pd.DataFrame(
        {
            "Year": [2023, 2023, 2023, 2024, 2024, 2024, 2025, 2025, 2025],
            "full": [1, 2, 3, 4, 5, 6, 7, 8, 9],
            "late": [1, 2, 3, None, None, None, None, None, None],
        }
    )


class TestCoverage:
    """Coverage is the weakest of the named columns, not their average."""

    def test_reports_the_worst_column(self, coverage_frame):
        assert utils.coverage(coverage_frame, ["full", "late"], 2023) == 1.0
        assert utils.coverage(coverage_frame, ["full", "late"], 2024) == 0.0

    def test_a_year_outside_the_data_has_no_coverage(self, coverage_frame):
        assert utils.coverage(coverage_frame, ["full"], 1999) == 0.0


class TestLatestCompleteYear:
    """The reference year is picked per indicator, not globally."""

    def test_returns_the_most_recent_year_that_clears_the_threshold(
        self, coverage_frame
    ):
        assert utils.latest_complete_year(coverage_frame, ["full"]) == 2025

    def test_skips_back_past_years_that_do_not_clear_it(self, coverage_frame):
        assert utils.latest_complete_year(coverage_frame, ["late"]) == 2023

    def test_raises_when_no_year_ever_clears_the_threshold(self):
        df = pd.DataFrame({"Year": [2024, 2024], "sparse": [1.0, None]})

        with pytest.raises(ValueError, match="trend view"):
            utils.latest_complete_year(df, ["sparse"])


class TestCoverageNote:
    """Snapshot charts state how many countries actually reported."""

    def test_counts_only_rows_complete_across_every_column(
        self, coverage_frame
    ):
        note = utils.coverage_note(coverage_frame, ["full", "late"], 2023)

        assert note == "3 of 3 countries reported in 2023"

    def test_reports_zero_when_the_column_is_empty_that_year(
        self, coverage_frame
    ):
        note = utils.coverage_note(coverage_frame, ["late"], 2025)

        assert note == "0 of 3 countries reported in 2025"


class TestCoverageByYear:
    """The per-year table is what makes an empty indicator visible at all."""

    def test_returns_a_fraction_per_year_and_column(self, coverage_frame):
        table = utils.coverage_by_year(coverage_frame, ["full", "late"])

        assert table.loc[2023, "late"] == 1.0
        assert table.loc[2024, "late"] == 0.0
        assert (table["full"] == 1.0).all()


class TestPanelNote:
    """All-years charts state the panel they rest on, as snapshots do."""

    def test_reports_countries_years_and_rows_after_a_listwise_drop(
        self, panel
    ):
        note = utils.panel_note(panel, ["score", "outcome"])

        assert note == "3 countries, 2001–2004, 12 country-years"

    def test_counts_only_rows_complete_across_every_column(self, panel):
        panel.loc[panel["Country Name"] == "C", "outcome"] = None

        note = utils.panel_note(panel, ["score", "outcome"])

        assert note == "2 countries, 2001–2004, 8 country-years"


class TestLog10Column:
    """The freedom-prosperity relationship is log-linear, not linear."""

    def test_takes_the_base_ten_log(self):
        result = utils.log10_column(pd.Series([1.0, 10.0, 1000.0]))

        assert result.tolist() == [0.0, 1.0, 3.0]

    @pytest.mark.parametrize("value", [0.0, -5.0, None])
    def test_returns_na_for_values_with_no_log(self, value):
        result = utils.log10_column(pd.Series([value]))

        assert result.isna().all()


class TestDemean:
    """Demeaning is what separates a within estimate from a pooled one."""

    def test_subtracts_the_group_mean(self):
        df = pd.DataFrame(
            {"g": ["a", "a", "b", "b"], "v": [1.0, 3.0, 10.0, 20.0]}
        )

        result = utils.demean(df, ["v"], "g")

        assert result["v"].tolist() == [-1.0, 1.0, -5.0, 5.0]

    def test_leaves_the_grouping_column_alone(self):
        df = pd.DataFrame({"g": ["a", "a"], "v": [1.0, 3.0]})

        result = utils.demean(df, ["v"], "g")

        assert result["g"].tolist() == ["a", "a"]

    def test_does_not_mutate_the_input(self):
        df = pd.DataFrame({"g": ["a", "a"], "v": [1.0, 3.0]})

        utils.demean(df, ["v"], "g")

        assert df["v"].tolist() == [1.0, 3.0]


class TestCorrelationDecomposition:
    """A pooled correlation averages two questions with different answers."""

    def test_between_and_within_can_disagree_in_sign(self, panel):
        result = utils.correlation_decomposition(panel, ["score"], "outcome")

        assert result.loc["score", "between"] > 0.9
        assert result.loc["score", "within"] < 0

    def test_the_pooled_figure_sits_between_the_two(self, panel):
        result = utils.correlation_decomposition(panel, ["score"], "outcome")

        row = result.loc["score"]
        assert row["within"] < row["pooled"] < row["between"]

    def test_counts_the_countries_behind_each_row(self, panel):
        result = utils.correlation_decomposition(panel, ["score"], "outcome")

        assert result.loc["score", "countries"] == 3

    def test_orders_components_by_the_between_correlation(self, panel):
        panel["mirror"] = -panel["score"]

        result = utils.correlation_decomposition(
            panel, ["mirror", "score"], "outcome"
        )

        assert result.index.tolist() == ["score", "mirror"]

    def test_skips_a_column_with_no_usable_rows(self, panel):
        panel["empty"] = None

        result = utils.correlation_decomposition(
            panel, ["score", "empty"], "outcome"
        )

        assert result.index.tolist() == ["score"]


class TestPeriodChange:
    """A change needs both endpoints, so one-sided countries are dropped."""

    def test_subtracts_the_start_year_from_the_end_year(self, panel):
        result = utils.period_change(panel, ["score", "outcome"], 2001, 2004)

        assert result.loc["A", "score"] == 30.0
        assert result.loc["A", "outcome"] == -3.0

    def test_drops_a_country_missing_one_endpoint(self, panel):
        late = pd.DataFrame(
            {
                "Country Name": ["D"],
                "Year": [2004],
                "score": [50.0],
                "outcome": [5.0],
            }
        )
        combined = pd.concat([panel, late], ignore_index=True)

        result = utils.period_change(
            combined, ["score", "outcome"], 2001, 2004
        )

        assert "D" not in result.index
        assert sorted(result.index) == ["A", "B", "C"]


class TestQuantileTransitions:
    """Mobility is measured against each year's own distribution."""

    @pytest.fixture
    def movers(self):
        """Six countries whose ranking reverses completely between years."""
        return pd.DataFrame(
            {
                "Country Name": list("ABCDEF") * 2,
                "Year": [2001] * 6 + [2024] * 6,
                "score": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
                + [6.0, 5.0, 4.0, 3.0, 2.0, 1.0],
            }
        )

    def test_counts_every_country_once(self, movers):
        matrix = utils.quantile_transitions(
            movers, "score", 2001, 2024, bands=3
        )

        assert matrix.to_numpy().sum() == 6

    def test_a_full_reversal_swaps_the_outer_bands(self, movers):
        matrix = utils.quantile_transitions(
            movers, "score", 2001, 2024, bands=3
        )

        # The middle band stays put by construction: its two members swap
        # with each other, which is movement the banding cannot see.
        assert matrix.loc["Q1", "Q3"] == 2
        assert matrix.loc["Q3", "Q1"] == 2
        assert matrix.loc["Q1", "Q1"] == 0

    def test_a_frozen_ranking_puts_everything_on_the_diagonal(self, movers):
        frozen = movers.copy()
        frozen.loc[frozen["Year"] == 2024, "score"] = [
            1.0,
            2.0,
            3.0,
            4.0,
            5.0,
            6.0,
        ]

        matrix = utils.quantile_transitions(
            frozen, "score", 2001, 2024, bands=3
        )

        assert matrix.to_numpy().trace() == 6

    def test_is_square_in_the_number_of_bands(self, movers):
        matrix = utils.quantile_transitions(
            movers, "score", 2001, 2024, bands=3
        )

        assert matrix.shape == (3, 3)
