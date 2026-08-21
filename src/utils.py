"""Generic helpers shared across the notebooks.

The coverage helpers exist because indicator availability in this dataset is
strongly year-dependent: the most recent year is complete for some columns and
entirely empty for others (life expectancy has no 2025 values at all). Picking
a single global `df["Year"].max()` therefore produces silently empty or
unrepresentative snapshots, so the reference year is chosen per indicator.

The panel helpers below serve the same honesty for statistics computed across
all years rather than in a single one: a country-year panel supports two quite
different correlations, and reporting only the pooled figure hides which of
them a claim actually rests on.
"""

import math

import pandas as pd


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


def panel_note(df, columns, group="Country Name", year_column="Year"):
    """Chart subtitle stating the panel behind an all-years statistic.

    The counterpart to `coverage_note` for charts that pool every year: the
    rows surviving a listwise drop vary a great deal by column (Labor Freedom
    is ~19.5% missing before 2009), so a correlation needs to say what it was
    computed on.
    """
    complete = df.dropna(subset=list(columns))

    return (
        f"{complete[group].nunique()} countries, "
        f"{complete[year_column].min()}–{complete[year_column].max()}, "
        f"{len(complete):,} country-years"
    )


def log10_column(series):
    """Base-10 log of a column, with non-positive values returned as NaN.

    Kept to the standard library rather than adding numpy to the project's
    declared dependencies: at a few thousand rows an elementwise map costs
    nothing, and the columns this is used on are strictly positive anyway.
    """
    return series.map(
        lambda value: (
            math.log10(value)
            if pd.notna(value) and value > 0
            else float("nan")
        )
    )


def demean(df, columns, by):
    """Subtract each group's mean from the named columns.

    Returns a new frame, so the same panel can be demeaned along a second
    dimension without the first pass being undone.
    """
    df = df.copy()
    for column in columns:
        df[column] = df[column] - df.groupby(by)[column].transform("mean")
    return df


def correlation_decomposition(
    df, columns, target, group="Country Name", year_column="Year"
):
    """Split each column's correlation with a target into between and within.

    Three numbers per column, because a country-year panel answers two
    different questions that a single `.corr()` silently averages together:

    - `pooled` treats every country-year as an independent observation,
      which is what a plain correlation reports.
    - `between` collapses each country to its long-run mean first, so it
      answers "do countries scoring higher tend to be richer?".
    - `within` removes both the country mean and the year mean, leaving only
      movement relative to a country's own average and to the global year.
      It answers "when a country's score moves, does its outcome move with
      it?". The year term is not optional here: GDP is in current US dollars
      and drifts upwards for everyone, which a country-only demeaning would
      leave in and mistake for signal.

    Sorted by `between` descending, so the ordering matches how the ranking
    is usually read.
    """
    rows = []
    for column in columns:
        panel = df[[group, year_column, column, target]].dropna()
        if panel.empty:
            continue

        means = panel.groupby(group)[[column, target]].mean()
        pair = [column, target]
        within = demean(demean(panel, pair, group), pair, year_column)

        rows.append(
            {
                "component": column,
                "pooled": panel[column].corr(panel[target]),
                "between": means[column].corr(means[target]),
                "within": within[column].corr(within[target]),
                "countries": panel[group].nunique(),
            }
        )

    return (
        pd.DataFrame(rows)
        .set_index("component")
        .sort_values("between", ascending=False)
    )


def period_change(
    df, columns, start_year, end_year, group="Country Name", year_column="Year"
):
    """Change in each column between two years, one row per country.

    Countries that do not report in both years are dropped rather than
    filled: a change needs both endpoints to mean anything, and carrying a
    one-sided country through would put it at the origin as if it had held
    still.
    """
    endpoints = df[df[year_column].isin([start_year, end_year])]

    changes = {}
    for column in columns:
        wide = endpoints.pivot_table(
            index=group, columns=year_column, values=column
        )
        if start_year in wide.columns and end_year in wide.columns:
            changes[column] = wide[end_year] - wide[start_year]

    return pd.DataFrame(changes).dropna()


def quantile_transitions(
    df,
    column,
    start_year,
    end_year,
    bands=5,
    group="Country Name",
    year_column="Year",
):
    """Count countries moving between quantile bands of a column.

    Each year is banded against its own distribution rather than against a
    fixed cut-off, so the matrix reads as mobility relative to the rest of
    the world. With a fixed threshold the global drift in scores would show
    up as movement even if every country held its place.
    """
    wide = (
        df[df[year_column].isin([start_year, end_year])]
        .pivot_table(index=group, columns=year_column, values=column)
        .dropna()
    )

    labels = [f"Q{band}" for band in range(1, bands + 1)]

    return pd.crosstab(
        pd.qcut(wide[start_year], bands, labels=labels),
        pd.qcut(wide[end_year], bands, labels=labels),
    )
