"""Generic helpers shared across the notebooks.

The coverage helpers exist because indicator availability in this dataset is
strongly year-dependent: the most recent year is complete for some columns and
entirely empty for others (life expectancy has no 2025 values at all). Picking
a single global `df["Year"].max()` therefore produces silently empty or
unrepresentative snapshots, so the reference year is chosen per indicator.
"""


def coverage_by_year(df, columns, year_column="Year"):
    """Fraction of non-null values per year, one column per named indicator."""
    return df.groupby(year_column)[list(columns)].apply(
        lambda group: group.notna().mean()
    )


def coverage(df, columns, year, year_column="Year"):
    """Lowest non-null fraction across the named columns in a single year."""
    snapshot = df[df[year_column] == year]
    if snapshot.empty:
        return 0.0
    return min(snapshot[column].notna().mean() for column in columns)


def latest_complete_year(df, columns, threshold=0.9, year_column="Year"):
    """Most recent year in which every column clears a coverage threshold.

    Raises rather than falling back to the latest year: a column that never
    reaches the threshold (secondary school enrollment peaks at ~71%) is not
    suited to a single-year snapshot at all, and silently substituting a
    different year would hide that.
    """
    for year in sorted(df[year_column].unique(), reverse=True):
        if coverage(df, columns, year, year_column) >= threshold:
            return year

    raise ValueError(
        f"No year reaches {threshold:.0%} coverage for all of "
        f"{list(columns)}. These columns need a trend view, not a snapshot."
    )


def coverage_note(df, columns, year, year_column="Year"):
    """Chart subtitle stating how many countries actually reported in a year.

    Snapshot charts otherwise drop non-reporting countries in silence; in 2025
    that quietly removes Liechtenstein, the highest GDP per capita in the
    dataset, from the top ten.
    """
    snapshot = df[df[year_column] == year]
    reported = snapshot[list(columns)].notna().all(axis=1).sum()

    return f"{reported} of {len(snapshot)} countries reported in {year}"
