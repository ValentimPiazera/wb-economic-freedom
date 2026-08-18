"""Reusable plotting helpers for the exploratory analysis notebook.

matplotlib is used for the static, portfolio-facing panels (it renders on
GitHub, which plotly's interactive output does not), and plotly.express for
the two animated charts where interactivity is the point.
"""

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import plotly.express as px
from adjustText import adjust_text
from matplotlib.ticker import FuncFormatter, LogLocator

# One shared palette, so every chart in the notebook reads as a single system.
PAPER = "#fcfcfb"
INK = "#0b0b0b"
MUTED = "#52514e"
FAINT = "#898781"
GRID = "#e1e0d9"
BACKDROP = "#d8d7d1"
ACCENT = "#2a78d6"
LEADER = "#c3c2b7"


def usd_short(value, _pos=None):
    """Format a GDP-per-capita tick as $850 / $2.5k / $100k."""
    return f"${value / 1000:g}k" if value >= 1000 else f"${value:g}"


def _strip_panel(ax, grid_axis="both"):
    """Apply the shared panel styling: no spines, soft grid, quiet ticks."""
    ax.set_facecolor(PAPER)
    ax.grid(True, axis=grid_axis, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(which="both", length=0, colors=FAINT, labelsize=9)
    for spine in ax.spines.values():
        spine.set_visible(False)


def _titles(ax, title, subtitle):
    """Left-aligned title with a muted subtitle sitting above the axes.

    Every snapshot chart carries its own coverage note as the subtitle, so a
    reader can see how many countries a given year actually reports rather
    than assuming the ranking is complete.
    """
    ax.set_title(
        title,
        fontsize=13,
        color=INK,
        loc="left",
        pad=22 if subtitle else 12,
    )
    if subtitle:
        ax.text(
            0,
            1.02,
            subtitle,
            transform=ax.transAxes,
            fontsize=9,
            color=FAINT,
            va="bottom",
        )


def plot_top_countries(
    df,
    value_col,
    year,
    title,
    xlabel,
    n=10,
    largest=True,
    color=ACCENT,
    label_col="Country Name",
    subtitle=None,
):
    """Horizontal bar chart of the highest or lowest countries in a year."""
    snapshot = df[df["Year"] == year]
    ranked = (
        snapshot.nlargest(n, value_col)
        if largest
        else snapshot.nsmallest(n, value_col)
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor(PAPER)
    ax.barh(ranked[label_col], ranked[value_col], color=color)
    ax.set_xlabel(xlabel, fontsize=10, color=MUTED)
    _titles(ax, title, subtitle)
    _strip_panel(ax, grid_axis="x")
    ax.invert_yaxis()
    fig.tight_layout()

    return fig


def plot_score_distribution(
    df,
    year,
    title,
    xlabel,
    value_col="Overall Score",
    bins=20,
    color="slateblue",
    subtitle=None,
):
    """Histogram showing how a score is spread across countries in one year."""
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor(PAPER)
    ax.hist(
        df[df["Year"] == year][value_col].dropna(),
        bins=bins,
        color=color,
        edgecolor=PAPER,
        linewidth=0.8,
    )
    ax.set_xlabel(xlabel, fontsize=10, color=MUTED)
    ax.set_ylabel("Number of Countries", fontsize=10, color=MUTED)
    _titles(ax, title, subtitle)
    _strip_panel(ax, grid_axis="y")
    fig.tight_layout()

    return fig


def scatter_freedom_development(df, y_col="GDP per capita (current US$)"):
    """Animated scatter of economic freedom against a development outcome."""
    return px.scatter(
        df,
        x="Overall Score",
        y=y_col,
        hover_name="Country Name",
        animation_frame="Year",
        log_y=True,
        range_y=[100, 250000],
        range_x=[0, 100],
        color=y_col,
    )


def choropleth_freedom(df, value_col="Overall Score"):
    """Animated world map of the economic freedom score by country."""
    fig = px.choropleth(
        df,
        locations="Country Code",
        color=value_col,
        hover_name="Country Name",
        animation_frame="Year",
        color_continuous_scale="RdYlGn",
    )

    fig.update_layout(
        width=1100,
        height=650,
        title={
            "text": f"{value_col} by Country",
            "x": 0.5,
            "xanchor": "center",
            "y": 0.95,
            "font": {"size": 25},
        },
    )
    fig.update_geos(projection_type="natural earth", showcoastlines=True)

    return fig


def plot_continent_overview(
    snapshot, continents, year, gdp_col, subtitle=None
):
    """Small-multiple grid of freedom vs GDP per capita, by continent.

    Each panel repeats every country as a faint backdrop, so the continents
    stay visually comparable rather than each being read in isolation.
    """
    fig, axes = plt.subplots(2, 3, figsize=(15, 9), sharex=True, sharey=True)
    fig.patch.set_facecolor(PAPER)

    # strict: the grid is sized for the six-continent model, so a mismatch
    # is a real problem and should fail rather than drop a panel silently.
    for ax, continent in zip(axes.flat, continents, strict=True):
        countries = snapshot[snapshot["Continent"] == continent]

        ax.scatter(
            snapshot["Overall Score"],
            snapshot[gdp_col],
            s=22,
            color=BACKDROP,
            edgecolor="none",
            zorder=1,
            label="All countries",
        )
        ax.scatter(
            countries["Overall Score"],
            countries[gdp_col],
            s=38,
            color=ACCENT,
            edgecolor=PAPER,
            linewidth=0.8,
            zorder=2,
            label="Countries in this continent",
        )

        ax.set_title(
            f"{continent}  ·  {len(countries)} countries",
            fontsize=12,
            color=INK,
            loc="left",
            pad=10,
        )
        ax.set_yscale("log")
        ax.set_yticks([1e2, 1e3, 1e4, 1e5])
        ax.set_yticklabels(["$100", "$1k", "$10k", "$100k"])
        _strip_panel(ax)

    fig.suptitle(
        f"Economic Freedom vs GDP per Capita by Continent ({year})",
        fontsize=16,
        color=INK,
        y=0.985,
    )
    if subtitle:
        fig.text(0.5, 0.945, subtitle, ha="center", fontsize=10, color=FAINT)
    fig.supxlabel("Economic Freedom Score", fontsize=11, color=MUTED)
    fig.supylabel(
        "GDP per Capita (current US$, log scale)", fontsize=11, color=MUTED
    )

    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper right",
        bbox_to_anchor=(0.99, 0.985),
        frameon=False,
        fontsize=10,
        labelcolor=MUTED,
        handletextpad=0.4,
        ncols=2,
    )

    fig.tight_layout(rect=[0.01, 0.02, 1, 0.93], h_pad=3)

    return fig


def plot_continent_detail(snapshot, continents, year, gdp_col, subtitle=None):
    """Larger per-continent panels with every country labelled by ISO3 code.

    Takes ~30s to render: the dense panels need the adjustText iterations to
    pull overlapping labels apart.
    """
    fig, axes = plt.subplots(3, 2, figsize=(15, 19))
    fig.patch.set_facecolor(PAPER)

    for ax, continent in zip(axes.flat, continents, strict=True):
        countries = snapshot[snapshot["Continent"] == continent]

        ax.scatter(
            countries["Overall Score"],
            countries[gdp_col],
            s=42,
            color=ACCENT,
            edgecolor=PAPER,
            linewidth=0.8,
            zorder=2,
        )
        # The halo keeps the codes legible where they cross leader lines.
        texts = [
            ax.text(
                row["Overall Score"],
                row[gdp_col],
                row["Country Code"],
                fontsize=7,
                color=MUTED,
                zorder=3,
                path_effects=[pe.withStroke(linewidth=2.5, foreground=PAPER)],
            )
            for _, row in countries.iterrows()
        ]

        ax.set_title(
            f"{continent}  ·  {len(countries)} countries",
            fontsize=13,
            color=INK,
            loc="left",
            pad=10,
        )
        ax.set_yscale("log")
        ax.yaxis.set_major_locator(LogLocator(base=10, subs=(1, 2, 5)))
        ax.yaxis.set_major_formatter(FuncFormatter(usd_short))
        ax.yaxis.set_minor_locator(LogLocator(base=10, subs=()))
        ax.margins(x=0.11, y=0.09)
        ax.set_xlabel("Economic Freedom Score", fontsize=9, color=MUTED)
        ax.set_ylabel("GDP per Capita (US$, log)", fontsize=9, color=MUTED)
        _strip_panel(ax)

        # Run last, so labels are nudged apart against the final axis scaling.
        adjust_text(
            texts,
            x=countries["Overall Score"].to_numpy(),
            y=countries[gdp_col].to_numpy(),
            ax=ax,
            expand=(1.25, 1.4),
            force_text=(0.4, 0.5),
            max_move=20,
            time_lim=8,
            arrowprops={"arrowstyle": "-", "color": LEADER, "linewidth": 0.5},
        )

    fig.suptitle(
        f"Economic Freedom vs GDP per Capita, within each continent ({year})",
        fontsize=17,
        color=INK,
        y=0.997,
    )
    if subtitle:
        fig.text(0.5, 0.982, subtitle, ha="center", fontsize=10, color=FAINT)

    fig.tight_layout(rect=[0, 0, 1, 0.975], h_pad=3.5, w_pad=3)

    return fig
