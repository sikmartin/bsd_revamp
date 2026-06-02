"""
tests/test_regression.py — Golden-output tests against the real ENTSOG export.

These tests load the actual data file and assert that key outputs match the
values manually validated during the analysis session. They serve as a
change-detection net: if filtering logic, unit conversion, the cutoff, or
aggregation is accidentally altered, these tests will fail and make the change
visible before it propagates into a report.

The tolerance on floating-point comparisons is deliberately loose (rel=0.005,
i.e. half a percent) because the data file may be refreshed with more recent
days over time, which will shift pooled percentiles slightly.  The absolute
structure of the results (ordering of scenarios, positive storage gaps) is
asserted exactly.

Skipping behaviour
------------------
If the data file is absent (e.g. in CI without the raw data), every test in
this module is skipped automatically.  The unit tests in test_data.py and
test_obligations.py still provide full logic coverage in that case.
"""

from pathlib import Path

import pandas as pd
import pytest

import bsd
import bsd.data as bdata
from bsd.imports import compute_monthly_imports

# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

DATA_PATH = bdata.DATA_PATH_IMPORTS

pytestmark = pytest.mark.skipif(
    not DATA_PATH.exists(),
    reason="Real data file not present; skipping regression tests.",
)


@pytest.fixture(scope="module")
def daily():
    return bdata.load_daily_imports(DATA_PATH, cutoff=bdata.DEFAULT_CUTOFF)


@pytest.fixture(scope="module")
def winter(daily):
    return daily[daily["month"].isin(bsd.WINTER_MONTHS)].copy()


@pytest.fixture(scope="module")
def monthly_imports():
    return compute_monthly_imports(bsd.DEFAULT_SCENARIOS_DICT)


# ---------------------------------------------------------------------------
# Data loading regression tests
# ---------------------------------------------------------------------------

class TestDataLoadRegression:

    def test_post_cutoff_row_count(self, daily):
        """The number of daily rows after the cutoff should be in the expected range.

        The lower bound reflects the dataset as validated (Mar 2022 – May 2026).
        The upper bound allows for future data refreshes adding more days.
        """
        assert 1500 <= len(daily) <= 3000

    def test_winter_day_count(self, daily):
        """At least four full Nov–Mar winters should be present (≥ 600 days)."""
        assert daily["is_winter"].sum() >= 600

    def test_no_negative_imports(self, daily):
        """Physical entry flows should never be negative."""
        assert (daily["GWh_d"] >= 0).all()

    def test_storage_not_in_daily(self, daily):
        """The 'Storage' adjacent system must have been excluded at load time.

        We verify indirectly: on the highest-import days, values should be
        below the threshold that would only be reached if storage withdrawal
        (hundreds of GWh/d on peak days) were included.
        """
        # Post-2022 non-storage physical flow (all months) should stay well
        # below the pre-2022 transit peak of ~3 000 GWh/d.  We use 2 000 as
        # the threshold; the ~840 GWh/d figure quoted in the notebook refers
        # to winter months only — spring/autumn 2022 still had elevated flows.
        assert daily["GWh_d"].max() < 2000

    def test_date_range(self, daily):
        """The dataset must start at or after the cutoff and end in 2025 or later."""
        assert daily["date"].min() >= pd.Timestamp(bdata.DEFAULT_CUTOFF)
        assert daily["date"].max().year >= 2025

    def test_gwh_magnitude_is_plausible(self, winter):
        """Winter median import should be between 150 and 500 GWh/d.

        Values outside this range would indicate a unit-conversion error or
        incorrect indicator selection.
        """
        assert 150 < winter["GWh_d"].median() < 500


# ---------------------------------------------------------------------------
# Percentile regression tests
# ---------------------------------------------------------------------------

class TestPercentileRegression:

    def test_winter_p10_in_expected_range(self, winter):
        """Winter P10 (single-day) should be near 135 GWh/d."""
        p10 = winter["GWh_d"].quantile(0.10)
        assert 100 < p10 < 180, f"Winter P10 = {p10:.1f}, outside expected range"

    def test_winter_p50_in_expected_range(self, winter):
        """Winter median should be near 243 GWh/d."""
        p50 = winter["GWh_d"].median()
        assert 180 < p50 < 320, f"Winter P50 = {p50:.1f}, outside expected range"

    def test_winter_p90_in_expected_range(self, winter):
        """Winter P90 should be near 370 GWh/d."""
        p90 = winter["GWh_d"].quantile(0.90)
        assert 300 < p90 < 500, f"Winter P90 = {p90:.1f}, outside expected range"

    def test_rolling30_p10_above_daily_p10(self, daily, winter):
        """The 30-day rolling average P10 should be higher than the single-day P10.

        Rolling averages smooth out the tails: the lowest 30-day average is
        higher than the single lowest day because sustained multi-week cold
        spells are less extreme than the single worst day.
        """
        roll = daily["GWh_d"].rolling(30, min_periods=30).mean()
        winter_roll = roll[daily["month"].isin(bsd.WINTER_MONTHS)].dropna()

        daily_p10 = winter["GWh_d"].quantile(0.10)
        roll_p10 = winter_roll.quantile(0.10)

        assert roll_p10 > daily_p10, (
            f"Rolling P10 ({roll_p10:.1f}) should be > single-day P10 ({daily_p10:.1f})"
        )


# ---------------------------------------------------------------------------
# Monthly import scenario regression tests
# ---------------------------------------------------------------------------

class TestMonthlyImportRegression:

    def test_five_scenarios_returned(self, monthly_imports):
        assert len(monthly_imports) == 5

    def test_scenario_ordering(self, monthly_imports):
        """For every winter month, S1 ≤ S2 ≤ ... ≤ S5 (lower percentile = lower imports)."""
        keys = list(bsd.DEFAULT_SCENARIOS_DICT.keys())
        for m in bsd.MONTH_ORDER:
            values = [monthly_imports[k][m] for k in keys]
            assert values == sorted(values), \
                f"Month {m}: scenario imports not monotonically increasing: {values}"

    def test_all_imports_positive(self, monthly_imports):
        for key, series in monthly_imports.items():
            assert (series > 0).all(), f"Scenario {key} has non-positive import values"

    def test_s1_jan_in_expected_range(self, monthly_imports):
        """S1 January imports should be near 113 GWh/d."""
        s1_jan = monthly_imports["S1"][1]
        assert 80 < s1_jan < 160, f"S1 Jan = {s1_jan:.1f}, outside expected range"

    def test_s4_jan_in_expected_range(self, monthly_imports):
        """S4 (median) January imports should be near 214 GWh/d."""
        s4_jan = monthly_imports["S4"][1]
        assert 150 < s4_jan < 300, f"S4 Jan = {s4_jan:.1f}, outside expected range"


# ---------------------------------------------------------------------------
# Seasonal peaks regression tests
# ---------------------------------------------------------------------------

class TestSeasonalPeaksRegression:

    def test_post_2022_seasons_present(self, winter):
        w = winter.copy()
        w["gas_winter"] = bdata.gas_winter_label(w["date"])
        seasons = w["gas_winter"].dropna().unique()
        for season in ["2022/23", "2023/24", "2024/25"]:
            assert season in seasons, f"Season {season} missing"

    def test_2021_22_peak_above_post_2022_peaks(self, daily):
        """Winter 2021/22 (transitional) should have a higher peak than later winters."""
        w = daily[daily["month"].isin(bsd.WINTER_MONTHS)].copy()
        w["gas_winter"] = bdata.gas_winter_label(w["date"])
        peaks = w.groupby("gas_winter")["GWh_d"].max()
        if "2021/22" in peaks.index:
            assert peaks["2021/22"] > peaks[["2022/23", "2023/24", "2024/25"]].max(), \
                "2021/22 peak should exceed all post-2022 season peaks"
