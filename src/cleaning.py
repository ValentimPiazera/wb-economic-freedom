"""Cleaning and merging transformations for the two raw sources.

Each function returns a new frame rather than mutating its input, so a
notebook cell can be re-run without compounding earlier edits.
"""

import pandas as pd
import pycountry_convert as pc

ROWS_TO_DROP = [
    "Data from database: World Development Indicators",
    "Last Updated: 07/01/2026",
    "American Samoa",
    "French Polynesia",
    "Isle of Man",
    "Virgin Islands (U.S.)",
    "Antigua and Barbuda",
    "Andorra",
    "Channel Islands",
    "Greenland",
    "Aruba",
    "Faroe Islands",
    "Monaco",
    "Northern Mariana Islands",
    "Marshall Islands",
    "West Bank and Gaza",
    "Tuvalu",
    "St. Kitts and Nevis",
    "Nauru",
    "Turks and Caicos Islands",
    "San Marino",
    "Bermuda",
    "Grenada",
    "Guam",
    "New Caledonia",
    "British Virgin Islands",
    "Curacao",
    "Palau",
    "St. Martin (French part)",
    "Sint Maarten (Dutch part)",
    "Puerto Rico (US)",
    "Gibraltar",
    "South Sudan",
    "Cayman Islands",
]

COUNTRY_NAME_MAPPING = {
    "Korea, Rep.": "South Korea",
    "Slovak Republic": "Slovakia",
    "Turkiye": "Türkiye",
    "Russian Federation": "Russia",
    "Hong Kong SAR, China": "Hong Kong",
    "Somalia, Fed. Rep.": "Somalia",
    "Venezuela, RB": "Venezuela",
    "Bahamas, The": "The Bahamas",
    "Syrian Arab Republic": "Syria",
    "Cote d'Ivoire": "Côte d'Ivoire",
    "Micronesia, Fed. Sts.": "Micronesia",
    "Myanmar": "Burma",
    "Gambia, The": "The Gambia",
    "Viet Nam": "Vietnam",
    "St. Vincent and the Grenadines": "Saint Vincent and the Grenadines",
    "Congo, Rep.": "Republic of Congo",
    "St. Lucia": "Saint Lucia",
    "Egypt, Arab Rep.": "Egypt",
    "Lao PDR": "Laos",
    "Congo, Dem. Rep.": "Democratic Republic of Congo",
    "Korea, Dem. People's Rep.": "North Korea",
    "Macao SAR, China": "Macau",
    "Czechia": "Czech Republic",
    "Yemen, Rep.": "Yemen",
    "Iran, Islamic Rep.": "Iran",
    "Sao Tome and Principe": "São Tomé and Príncipe",
    "Philippines": "The Philippines",
}

# The two ISO3 codes in this dataset that pycountry_convert cannot resolve:
# XKX (Kosovo) is a user-assigned code rather than an official ISO one, and TLS
# (Timor-Leste) is missing from the library's alpha-2 to continent table.
CONTINENT_OVERRIDES = {
    "XKX": "Europe",
    "TLS": "Asia",
}

WB_NUMERIC_COLS = [
    "Carbon dioxide (CO2) emissions (total) excluding LULUCF (Mt CO2e)",
    "Foreign direct investment, net inflows (% of GDP)",
    "GDP growth (annual %)",
    "Inflation, consumer prices (annual %)",
    "Life expectancy at birth, total (years)",
    "Poverty headcount ratio at $3.00 a day (2021 PPP) (% of population)",
    "School enrollment, secondary (% gross)",
    "Unemployment, total (% of total labor force) (modeled ILO estimate)",
]


def compare_countries(
    df1, df2, col1, col2, label1="Dataset 1", label2="Dataset 2"
):
    """Compare and print unmatched countries between two datasets."""
    set1 = set(df1[col1].unique())
    set2 = set(df2[col2].unique())

    only_in_df1 = set1 - set2
    only_in_df2 = set2 - set1

    print(f"Only in {label1}: {only_in_df1}")
    print(f"Only in {label2}: {only_in_df2}")

    return only_in_df1, only_in_df2


def standardise_country_names(df, column, mapping=COUNTRY_NAME_MAPPING):
    """Standardise country names in a column using a fixed mapping."""
    df = df.copy()
    df[column] = df[column].replace(mapping)
    return df


def drop_unmatched_countries(df, column, values_to_drop):
    """Remove country values that have no match in the other dataset.

    Covers junk rows, territories, and countries without coverage in both
    sources.
    """
    df = df.copy()
    df = df[~df[column].isin(values_to_drop)]
    return df


def melt_years(df, id_vars, var_name="Year", value_name="Value"):
    """Melt the year columns into long format.

    The Year column is cleaned into a proper integer along the way
    (e.g. "2001 [YR2001]" -> 2001).
    """
    df = df.copy()

    year_columns = [col for col in df.columns if col not in id_vars]

    df_long = df.melt(
        id_vars=id_vars,
        value_vars=year_columns,
        var_name=var_name,
        value_name=value_name,
    )

    df_long[var_name] = df_long[var_name].str.extract(r"(\d{4})").astype(int)

    return df_long


def pivot_indicators(
    df, index_cols, columns_col="Series Name", values_col="Value"
):
    """Pivot indicator rows into columns.

    Produces one row per country-year combination.
    """
    df_wide = df.pivot_table(
        index=index_cols,
        columns=columns_col,
        values=values_col,
        aggfunc="first",
    ).reset_index()

    df_wide.columns.name = None

    return df_wide


def code_to_continent(code, overrides=CONTINENT_OVERRIDES):
    """Resolve a single ISO3 country code to a continent name.

    Returns NA when pycountry_convert has no entry for the code and no
    override is defined, rather than raising.
    """
    if pd.isna(code):
        return pd.NA

    if code in overrides:
        return overrides[code]

    # pycountry_convert raises KeyError for codes it does not know, but
    # TypeError for anything that is not a well-formed code string.
    try:
        alpha2 = pc.country_alpha3_to_country_alpha2(code)
        continent_code = pc.country_alpha2_to_continent_code(alpha2)
    except (KeyError, TypeError):
        return pd.NA

    return pc.convert_continent_code_to_continent_name(continent_code)


def add_continent_column(
    df, code_column="Country Code", continent_column="Continent"
):
    """Add a continent column derived from each row's ISO3 country code.

    pycountry_convert follows the conventional six-continent model, in line
    with the UN M49 geoscheme: Central America and the Caribbean fall under
    North America, and transcontinental states are classified by their M49
    region (Russia as Europe; Türkiye, Cyprus, Georgia, Armenia and Azerbaijan
    as Asia).
    """
    df = df.copy()
    df[continent_column] = df[code_column].map(code_to_continent)
    return df


def convert_columns_to_numeric(df, columns):
    """Convert the given columns to numeric.

    Removes thousand separators and coerces the World Bank null marker
    ('..') to NaN.
    """
    df = df.copy()
    for col in columns:
        df[col] = pd.to_numeric(
            df[col].astype(str).str.replace(",", ""), errors="coerce"
        )
    return df
