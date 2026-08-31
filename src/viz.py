"""Reusable plotting helpers for the exploratory analysis notebook.

matplotlib is used for the static, portfolio-facing panels (it renders on
GitHub, which plotly's interactive output does not), and plotly.express for
the two animated charts where interactivity is the point.
"""

from pathlib import Path

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import plotly.express as px
from adjustText import adjust_text
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import FuncFormatter, LogLocator, MaxNLocator

# Resolved from the repository root, which is where the notebooks run.
FIGURE_DIR = Path("figures")

# One shared palette, so every chart in the notebook reads as a single system.
PAPER = "#fcfcfb"
INK = "#0b0b0b"
MUTED = "#52514e"
FAINT = "#898781"
GRID = "#e1e0d9"
BACKDROP = "#d8d7d1"
ACCENT = "#2a78d6"
LEADER = "#c3c2b7"

# The counterweight to ACCENT, for the correlation panels: two of the freedom
# sub-components correlate negatively with prosperity, and a chart that draws
# them in the same blue as the rest buries the most surprising thing in it.
ACCENT_NEG = "#c2492f"

HEAT = LinearSegmentedColormap.from_list("paper_accent", [PAPER, ACCENT])


def usd_short(value, _pos=None):
    """Format a GDP-per-capita tick as $850 / $2.5k / $100k."""
    return f"${value / 1000:g}k" if value >= 1000 else f"${value:g}"


def log10_multiple(value, _pos=None):
    """Format a log10 change as the multiple it stands for (0.5 -> x3.2).

    A change chart in log units is unreadable without this: nothing about
    "0.5" says "three times richer", which is the whole claim.
    """
    return f"×{10**value:.2g}"


def save_figure(fig, name, directory=FIGURE_DIR, dpi=150):
    """Write a figure to `figures/`, returning the path written.

    Called just before `plt.show()` so an exported panel cannot drift from
    the notebook that produced it: re-running the notebook rewrites every
    file it is responsible for, the same discipline the committed cell
    outputs already follow. Saving has to come first, because the inline
    backend closes the figure once it has been shown.

    Deliberately does not display the figure itself. `plt.show()` stays the
    last statement in the cell so the notebook renders the chart rather than
    the repr of the path returned here.

    The saved file carries the figure's own background rather than
    matplotlib's default white, so the PNG matches the panel as it appears
    in the notebook.
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{name}.png"

    fig.savefig(path, dpi=dpi, facecolor=fig.get_facecolor())

    return path


def save_plotly_figure(
    fig, name, directory=FIGURE_DIR, width=1100, height=650, scale=2
):
    """Write a plotly figure to `figures/` as a static PNG.

    A still, and only ever a still. Both plotly charts in the analysis run
    across 25 years, and interactivity — hovering a point to find out which
    country it is — is the reason they exist at all. The exported image
    keeps them visible on GitHub, where plotly does not render; it is not a
    substitute for opening the notebook.

    Goes through `kaleido`, which is what plotly shells out to for static
    export and why it is a declared dependency.
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{name}.png"

    fig.write_image(path, width=width, height=height, scale=scale)

    return path


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


def scatter_freedom_development(
    df, y_col="GDP per capita (current US$)", year=None
):
    """Animated scatter of economic freedom against a development outcome.

    Passing `year` drops the animation and returns that single year. Only
    the static export uses it: a PNG can hold one frame, and the frame
    plotly would otherwise write is 2001, the sparsest year in the panel.
    """
    frame = df if year is None else df[df["Year"] == year]

    return px.scatter(
        frame,
        x="Overall Score",
        y=y_col,
        hover_name="Country Name",
        animation_frame=None if year else "Year",
        log_y=True,
        range_y=[100, 250000],
        range_x=[0, 100],
        color=y_col,
    )


def choropleth_freedom(df, value_col="Overall Score", year=None):
    """Animated world map of the economic freedom score by country.

    Passing `year` drops the animation and returns that single year, for
    the same reason as `scatter_freedom_development`.
    """
    frame = df if year is None else df[df["Year"] == year]
    title = f"{value_col} by Country"

    fig = px.choropleth(
        frame,
        locations="Country Code",
        color=value_col,
        hover_name="Country Name",
        animation_frame=None if year else "Year",
        color_continuous_scale="RdYlGn",
    )

    fig.update_layout(
        width=1100,
        height=650,
        title={
            "text": f"{title} ({year})" if year else title,
            "x": 0.5,
            "xanchor": "center",
            "y": 0.95,
            "font": {"size": 25},
        },
    )
    fig.update_geos(projection_type="natural earth", showcoastlines=True)

    return fig


def plot_correlation_decomposition(
    decomposition,
    title,
    xlabel="Correlation with the outcome",
    subtitle=None,
):
    """Dumbbell chart contrasting between-country and within-country r.

    Takes the frame returned by `utils.correlation_decomposition`. The gap
    between the two dots on each row is the point of the chart: it is the
    share of a pooled correlation that comes from comparing countries with
    one another rather than from watching any country actually change.

    The between-country dot is drawn in ACCENT_NEG where it falls below
    zero, because the two components that reverse sign are easy to miss in a
    single-colour ranking.
    """
    # Reversed so the strongest correlation lands at the top, as in barh.
    order = decomposition.iloc[::-1].assign(row=range(len(decomposition)))
    positive = order[order["between"] >= 0]
    negative = order[order["between"] < 0]

    fig, ax = plt.subplots(figsize=(10, 6.5))
    fig.patch.set_facecolor(PAPER)

    ax.axvline(0, color=MUTED, linewidth=1, zorder=2)
    ax.hlines(
        order["row"],
        order["within"],
        order["between"],
        color=GRID,
        linewidth=2.5,
        zorder=3,
    )
    ax.scatter(
        order["within"],
        order["row"],
        s=55,
        color=FAINT,
        edgecolor=PAPER,
        linewidth=1,
        zorder=4,
        label="Within country (country and year effects removed)",
    )
    ax.scatter(
        positive["between"],
        positive["row"],
        s=95,
        color=ACCENT,
        edgecolor=PAPER,
        linewidth=1,
        zorder=5,
        label="Between countries (long-run means)",
    )
    if not negative.empty:
        ax.scatter(
            negative["between"],
            negative["row"],
            s=95,
            color=ACCENT_NEG,
            edgecolor=PAPER,
            linewidth=1,
            zorder=5,
            label="Between countries, negative",
        )

    ax.set_yticks(order["row"])
    ax.set_yticklabels(order.index, fontsize=10, color=MUTED)
    ax.set_xlabel(xlabel, fontsize=10, color=MUTED)
    ax.margins(y=0.05)
    _titles(ax, title, subtitle)
    _strip_panel(ax, grid_axis="x")
    ax.legend(
        loc="lower right",
        frameon=False,
        fontsize=9,
        labelcolor=MUTED,
        handletextpad=0.4,
    )
    fig.tight_layout()

    return fig


def plot_change_scatter(
    changes,
    x_col,
    y_col,
    title,
    xlabel,
    ylabel,
    n_labels=8,
    subtitle=None,
    y_formatter=None,
):
    """Scatter of two period changes, with the largest movers labelled.

    Takes the frame returned by `utils.period_change`. Only the extremes
    carry labels: at ~150 countries a fully labelled panel is unreadable,
    and the argument rests on who moved furthest rather than on the middle
    of the pack.

    Pass `y_formatter=log10_multiple` when the y axis is a log change, so
    the ticks read as multiples rather than as bare log units.
    """
    movers = set(changes.nlargest(n_labels, x_col).index) | set(
        changes.nsmallest(n_labels, x_col).index
    )

    gained = changes[changes[x_col] >= 0]
    lost = changes[changes[x_col] < 0]

    fig, ax = plt.subplots(figsize=(10, 7))
    fig.patch.set_facecolor(PAPER)

    ax.axhline(0, color=GRID, linewidth=1.2, zorder=1)
    ax.axvline(0, color=GRID, linewidth=1.2, zorder=1)
    for subset, colour in ((gained, ACCENT), (lost, ACCENT_NEG)):
        ax.scatter(
            subset[x_col],
            subset[y_col],
            s=42,
            color=colour,
            edgecolor=PAPER,
            linewidth=0.8,
            zorder=3,
        )

    labelled = changes.loc[sorted(movers)]
    texts = [
        ax.text(
            row[x_col],
            row[y_col],
            country,
            fontsize=8,
            color=INK,
            zorder=4,
            path_effects=[pe.withStroke(linewidth=2.5, foreground=PAPER)],
        )
        for country, row in labelled.iterrows()
    ]

    ax.set_xlabel(xlabel, fontsize=10, color=MUTED)
    ax.set_ylabel(ylabel, fontsize=10, color=MUTED)
    ax.margins(0.08)
    if y_formatter:
        ax.yaxis.set_major_formatter(FuncFormatter(y_formatter))
    _titles(ax, title, subtitle)
    _strip_panel(ax)

    # Run last, so labels are nudged apart against the final axis scaling.
    adjust_text(
        texts,
        x=labelled[x_col].to_numpy(),
        y=labelled[y_col].to_numpy(),
        ax=ax,
        expand=(1.3, 1.5),
        force_text=(0.4, 0.6),
        max_move=25,
        time_lim=6,
        arrowprops={"arrowstyle": "-", "color": LEADER, "linewidth": 0.5},
    )
    fig.tight_layout()

    return fig


def plot_transition_matrix(
    matrix, title, xlabel, ylabel, subtitle=None, cmap=HEAT
):
    """Heatmap of counts moving between bands, with the diagonal outlined.

    Takes the crosstab returned by `utils.quantile_transitions`. The
    outlined diagonal is what the eye should land on first: everything on it
    is a country that held its place relative to the rest of the world.
    """
    fig, ax = plt.subplots(figsize=(8, 6.5))
    fig.patch.set_facecolor(PAPER)

    values = matrix.to_numpy()
    mesh = ax.imshow(values, cmap=cmap, aspect="auto")

    # Annotate every cell: the counts are the substance, the shading is only
    # there to make the diagonal readable at a glance.
    threshold = values.max() * 0.6
    for row in range(values.shape[0]):
        for col in range(values.shape[1]):
            ax.text(
                col,
                row,
                values[row, col],
                ha="center",
                va="center",
                fontsize=11,
                color=PAPER if values[row, col] > threshold else INK,
            )
        ax.add_patch(
            plt.Rectangle(
                (row - 0.5, row - 0.5),
                1,
                1,
                fill=False,
                edgecolor=ACCENT_NEG,
                linewidth=2,
            )
        )

    ax.set_xticks(range(len(matrix.columns)), matrix.columns, fontsize=10)
    ax.set_yticks(range(len(matrix.index)), matrix.index, fontsize=10)
    ax.set_xlabel(xlabel, fontsize=10, color=MUTED)
    ax.set_ylabel(ylabel, fontsize=10, color=MUTED)
    _titles(ax, title, subtitle)
    ax.grid(False)
    ax.tick_params(which="both", length=0, colors=FAINT)
    for spine in ax.spines.values():
        spine.set_visible(False)

    bar = fig.colorbar(mesh, ax=ax, shrink=0.8)
    # Counts, so half a country on the scale would be nonsense.
    bar.locator = MaxNLocator(integer=True)
    bar.update_ticks()
    bar.set_label("Number of countries", fontsize=9, color=MUTED)
    bar.outline.set_visible(False)
    bar.ax.tick_params(length=0, colors=FAINT, labelsize=9)

    fig.tight_layout()

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
