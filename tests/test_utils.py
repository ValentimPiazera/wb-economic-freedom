"""Tests for the coverage helpers in `src/utils.py`."""

import pandas as pd
import pytest

from src import utils


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
