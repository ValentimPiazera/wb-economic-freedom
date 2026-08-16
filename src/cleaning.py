import pandas as pd

rows_to_drop = [
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

# Continent groupings follow the UN M49 geoscheme, mapped to the conventional
# six-continent model (Central America and the Caribbean under North America,
# transcontinental states classified by their UN M49 region: e.g. Russia is
# Europe, while Turkey, Cyprus, Georgia, Armenia and Azerbaijan are Asia).
COUNTRY_CONTINENT_MAPPING = {
    # Africa
    "AGO": "Africa", "BDI": "Africa", "BEN": "Africa", "BFA": "Africa",
    "BWA": "Africa", "CAF": "Africa", "CIV": "Africa", "CMR": "Africa",
    "COD": "Africa", "COG": "Africa", "COM": "Africa", "CPV": "Africa",
    "DJI": "Africa", "DZA": "Africa", "EGY": "Africa", "ERI": "Africa",
    "ETH": "Africa", "GAB": "Africa", "GHA": "Africa", "GIN": "Africa",
    "GMB": "Africa", "GNB": "Africa", "GNQ": "Africa", "KEN": "Africa",
    "LBR": "Africa", "LBY": "Africa", "LSO": "Africa", "MAR": "Africa",
    "MDG": "Africa", "MLI": "Africa", "MOZ": "Africa", "MRT": "Africa",
    "MUS": "Africa", "MWI": "Africa", "NAM": "Africa", "NER": "Africa",
    "NGA": "Africa", "RWA": "Africa", "SDN": "Africa", "SEN": "Africa",
    "SLE": "Africa", "SOM": "Africa", "STP": "Africa", "SWZ": "Africa",
    "SYC": "Africa", "TCD": "Africa", "TGO": "Africa", "TUN": "Africa",
    "TZA": "Africa", "UGA": "Africa", "ZAF": "Africa", "ZMB": "Africa",
    "ZWE": "Africa",
    # Asia
    "AFG": "Asia", "ARE": "Asia", "ARM": "Asia", "AZE": "Asia",
    "BGD": "Asia", "BHR": "Asia", "BRN": "Asia", "BTN": "Asia",
    "CHN": "Asia", "CYP": "Asia", "GEO": "Asia", "HKG": "Asia",
    "IDN": "Asia", "IND": "Asia", "IRN": "Asia", "IRQ": "Asia",
    "ISR": "Asia", "JOR": "Asia", "JPN": "Asia", "KAZ": "Asia",
    "KGZ": "Asia", "KHM": "Asia", "KOR": "Asia", "KWT": "Asia",
    "LAO": "Asia", "LBN": "Asia", "LKA": "Asia", "MAC": "Asia",
    "MDV": "Asia", "MMR": "Asia", "MNG": "Asia", "MYS": "Asia",
    "NPL": "Asia", "OMN": "Asia", "PAK": "Asia", "PHL": "Asia",
    "PRK": "Asia", "QAT": "Asia", "SAU": "Asia", "SGP": "Asia",
    "SYR": "Asia", "THA": "Asia", "TJK": "Asia", "TKM": "Asia",
    "TLS": "Asia", "TUR": "Asia", "UZB": "Asia", "VNM": "Asia",
    "YEM": "Asia",
    # Europe
    "ALB": "Europe", "AUT": "Europe", "BEL": "Europe", "BGR": "Europe",
    "BIH": "Europe", "BLR": "Europe", "CHE": "Europe", "CZE": "Europe",
    "DEU": "Europe", "DNK": "Europe", "ESP": "Europe", "EST": "Europe",
    "FIN": "Europe", "FRA": "Europe", "GBR": "Europe", "GRC": "Europe",
    "HRV": "Europe", "HUN": "Europe", "IRL": "Europe", "ISL": "Europe",
    "ITA": "Europe", "LIE": "Europe", "LTU": "Europe", "LUX": "Europe",
    "LVA": "Europe", "MDA": "Europe", "MKD": "Europe", "MLT": "Europe",
    "MNE": "Europe", "NLD": "Europe", "NOR": "Europe", "POL": "Europe",
    "PRT": "Europe", "ROU": "Europe", "RUS": "Europe", "SRB": "Europe",
    "SVK": "Europe", "SVN": "Europe", "SWE": "Europe", "UKR": "Europe",
    "XKX": "Europe",
    # North America
    "BHS": "North America", "BLZ": "North America", "BRB": "North America",
    "CAN": "North America", "CRI": "North America", "CUB": "North America",
    "DMA": "North America", "DOM": "North America", "GTM": "North America",
    "HND": "North America", "HTI": "North America", "JAM": "North America",
    "LCA": "North America", "MEX": "North America", "NIC": "North America",
    "PAN": "North America", "SLV": "North America", "TTO": "North America",
    "USA": "North America", "VCT": "North America",
    # South America
    "ARG": "South America", "BOL": "South America", "BRA": "South America",
    "CHL": "South America", "COL": "South America", "ECU": "South America",
    "GUY": "South America", "PER": "South America", "PRY": "South America",
    "SUR": "South America", "URY": "South America", "VEN": "South America",
    # Oceania
    "AUS": "Oceania", "FJI": "Oceania", "FSM": "Oceania", "KIR": "Oceania",
    "NZL": "Oceania", "PNG": "Oceania", "SLB": "Oceania", "TON": "Oceania",
    "VUT": "Oceania", "WSM": "Oceania",
}

wb_numeric_cols = [
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
    """Compares and prints unmatched countries between two datasets."""
    set1 = set(df1[col1].unique())
    set2 = set(df2[col2].unique())

    only_in_df1 = set1 - set2
    only_in_df2 = set2 - set1

    print(f"Only in {label1}: {only_in_df1}")
    print(f"Only in {label2}: {only_in_df2}")

    return only_in_df1, only_in_df2


def standardise_country_names(df, column, mapping=COUNTRY_NAME_MAPPING):
    """Standardise country names in a DataFrame column using a fixed mapping."""
    df = df.copy()
    df[column] = df[column].replace(mapping)
    return df


def drop_unmatched_countries(df, column, values_to_drop):
    """Remove rows with country values that have no match in the other dataset
    (junk rows, territories, or countries without coverage in both sources)."""
    df = df.copy()
    df = df[~df[column].isin(values_to_drop)]
    return df


def melt_years(df, id_vars, var_name="Year", value_name="Value"):
    """Melts year columns into long format and clean the Year column
    into a proper integer (e.g. "2001 [YR2001]" -> 2001)."""
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
    """Pivot indicator rows into columns, producing one row per
    country-year combination."""
    df_wide = df.pivot_table(
        index=index_cols,
        columns=columns_col,
        values=values_col,
        aggfunc="first",
    ).reset_index()

    df_wide.columns.name = None

    return df_wide


def add_continent_column(
    df,
    code_column="Country Code",
    continent_column="Continent",
    mapping=COUNTRY_CONTINENT_MAPPING,
):
    """Add a continent column derived from each row's ISO3 country code."""
    df = df.copy()
    df[continent_column] = df[code_column].map(mapping)
    return df


def convert_columns_to_numeric(df, columns):
    """Convert specified columns to numeric, removing thousand separators
    and coercing non-numeric values (e.g. '..') to NaN."""
    df = df.copy()
    for col in columns:
        df[col] = pd.to_numeric(
            df[col].astype(str).str.replace(",", ""), errors="coerce"
        )
    return df
