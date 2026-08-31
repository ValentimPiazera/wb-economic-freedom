"""Tests for the non-drawing helpers in `src/viz.py`.

The chart functions themselves are not tested: asserting on the appearance
of a matplotlib panel pins down pixels rather than meaning, and the panels
are reviewed by looking at them. What is covered here is the behaviour that
can go wrong without anyone noticing — the tick formatters and the figure
export.
"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402

from src import viz  # noqa: E402


@pytest.fixture
def figure():
    """A throwaway figure, closed again once the test has finished."""
    fig, _ = plt.subplots()
    yield fig
    plt.close(fig)


class TestUsdShort:
    """GDP-per-capita ticks have to stay readable across four orders."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [(850, "$850"), (2500, "$2.5k"), (100000, "$100k")],
    )
    def test_formats_by_magnitude(self, value, expected):
        assert viz.usd_short(value) == expected


class TestLog10Multiple:
    """A log change means nothing to a reader until it reads as a multiple."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [(0.0, "×1"), (1.0, "×10"), (2.0, "×1e+02")],
    )
    def test_converts_a_log_change_to_a_multiple(self, value, expected):
        assert viz.log10_multiple(value) == expected

    def test_a_negative_change_reads_below_one(self):
        assert viz.log10_multiple(-1.0) == "×0.1"


class TestSinglYearPlotlyCharts:
    """The static export needs one frame, not the animation."""

    @pytest.fixture
    def panel(self):
        """Two countries across two years, enough to tell frames apart."""
        return pd.DataFrame(
            {
                "Country Name": ["Portugal", "Brazil"] * 2,
                "Country Code": ["PRT", "BRA"] * 2,
                "Year": [2001, 2001, 2025, 2025],
                "Overall Score": [60.0, 55.0, 70.0, 50.0],
                "GDP per capita (current US$)": [
                    12000.0,
                    3000.0,
                    27000.0,
                    9000.0,
                ],
            }
        )

    def test_the_scatter_animates_when_no_year_is_given(self, panel):
        fig = viz.scatter_freedom_development(panel)

        assert fig.frames

    def test_passing_a_year_drops_the_animation(self, panel):
        fig = viz.scatter_freedom_development(panel, year=2025)

        assert not fig.frames

    def test_passing_a_year_keeps_only_that_year(self, panel):
        fig = viz.scatter_freedom_development(panel, year=2025)

        assert sorted(fig.data[0].x) == [50.0, 70.0]

    def test_the_choropleth_animates_when_no_year_is_given(self, panel):
        assert viz.choropleth_freedom(panel).frames

    def test_the_choropleth_year_reaches_the_title(self, panel):
        fig = viz.choropleth_freedom(panel, year=2025)

        assert not fig.frames
        assert "2025" in fig.layout.title.text


class TestSaveFigure:
    """Exported panels are rewritten by the notebook, not copied by hand."""

    def test_writes_a_png_named_after_the_chart(self, figure, tmp_path):
        path = viz.save_figure(figure, "some-chart", tmp_path)

        assert path == tmp_path / "some-chart.png"
        assert path.read_bytes().startswith(b"\x89PNG")

    def test_creates_the_directory_when_it_is_missing(self, figure, tmp_path):
        target = tmp_path / "reports" / "figures"

        viz.save_figure(figure, "some-chart", target)

        assert (target / "some-chart.png").exists()

    def test_overwrites_a_stale_file_rather_than_accumulating(
        self, figure, tmp_path
    ):
        viz.save_figure(figure, "some-chart", tmp_path)
        viz.save_figure(figure, "some-chart", tmp_path)

        assert len(list(tmp_path.glob("*.png"))) == 1

    def test_does_not_display_the_figure_itself(self, figure, tmp_path):
        # plt.show() stays the notebook's last statement, so a cell renders
        # the chart rather than the repr of the path returned here.
        result = viz.save_figure(figure, "some-chart", tmp_path)

        assert result is not None
        assert plt.fignum_exists(figure.number)

    def test_defaults_to_the_figures_directory(self):
        assert viz.FIGURE_DIR.as_posix() == "figures"
