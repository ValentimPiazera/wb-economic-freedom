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
