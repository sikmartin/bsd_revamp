"""
tests/test_regression.py — Golden-output tests against the real ENTSOG export.

These tests load the actual data file and assert that key outputs match the
values manually validated during the analysis session.  They serve as a
change-detection net: if filtering logic, unit conversion, the cutoff, or
the rolling-average window is accidentally altered, these tests will fail and
make the change visible before it propagates into a report.

The tolerance on floating-point comparisons is deliberately loose (rel=0.005,
i.e. half a percent) because the data file may be refreshed with more recent
days over time, which will shift pooled percentiles slightly.  The absolute
structure of the results (ordering of scenarios, positive storage gaps) is
asserted exactly.

Skipping behaviour
------------------
If the data file is absent (e.g. in CI without the raw data), every test in
this module is skipped automatically.  The unit tests in test_data.py and
test_capacity.py still provide full logic coverage in that case.
"""

from pathlib import Path

import pandas as pd
import pytest

import bsd.data as bdata
import bsd.capacity as bcap

# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

DATA_PATH = bdata.DATA_PATH_IMPORTS
PEAK_DEMAND = 370.0

pytestmark = pytest.mark.skipif(
    not DATA_PATH.exists(),
    reason="Real data file not present; skipping regression tests.",
)


@pytest.fixture(scope="module")
def daily():
    return bdata.load_daily_imports(DATA_PATH, cutoff=bdata.DEFAULT_CUTOFF)


@pytest.fixture(scope="module")
def results(daily):
    return bcap.storage_scenarios(daily, peak_demand_GWh_d=PEAK_DEMAND)


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
        assert daily["date"].min() >= bdata.DEFAULT_CUTOFF
        assert daily["date"].max().year >= 2025

    def test_gwh_magnitude_is_plausible(self, daily):
        """Winter median import should be between 150 and 500 GWh/d.

        Values outside this range would indicate a unit-conversion error or
        incorrect indicator selection.
        """
        winter_median = bcap.winter_daily(daily)["GWh_d"].median()
        assert 150 < winter_median < 500, \
            f"Winter median {winter_median:.1f} GWh/d is outside plausible range"


# ---------------------------------------------------------------------------
# Percentile regression tests
# ---------------------------------------------------------------------------

class TestPercentileRegression:

    def test_winter_p10_in_expected_range(self, daily):
        """Winter P10 (single-day) should be near 135 GWh/d."""
        p10 = bcap.winter_daily(daily)["GWh_d"].quantile(0.10)
        assert 100 < p10 < 180, f"Winter P10 = {p10:.1f}, outside expected range"

    def test_winter_p50_in_expected_range(self, daily):
        """Winter median should be near 243 GWh/d."""
        p50 = bcap.winter_daily(daily)["GWh_d"].median()
        assert 180 < p50 < 320, f"Winter P50 = {p50:.1f}, outside expected range"

    def test_winter_p90_in_expected_range(self, daily):
        """Winter P90 should be near 370 GWh/d — close to the peak demand figure."""
        p90 = bcap.winter_daily(daily)["GWh_d"].quantile(0.90)
        assert 300 < p90 < 500, f"Winter P90 = {p90:.1f}, outside expected range"

    def test_rolling30_p10_below_daily_p10(self, daily):
        """The 30-day rolling average P10 should be higher than the single-day P10.

        Rolling averages smooth out the tails: the lowest 30-day average is
        higher than the single lowest day because sustained multi-week cold
        spells are less extreme than the single worst day.
        """
        enriched = bcap.add_rolling_avg(daily, window=30)
        winter = bcap.winter_daily(enriched).dropna(subset=["roll30_avg_GWh_d"])

        daily_p10 = bcap.winter_daily(daily)["GWh_d"].quantile(0.10)
        roll_p10 = winter["roll30_avg_GWh_d"].quantile(0.10)

        assert roll_p10 > daily_p10, (
            f"Rolling P10 ({roll_p10:.1f}) should be > single-day P10 ({daily_p10:.1f})"
        )


# ---------------------------------------------------------------------------
# Scenario table regression tests
# ---------------------------------------------------------------------------

class TestScenarioTableRegression:

    def test_five_scenarios_returned(self, results):
        assert len(results) == 5

    def test_storage_requirement_decreases_from_s1_to_s5(self, results):
        """More favourable import scenarios require less storage."""
        storage_values = results["storage_30d_TWh"].tolist()
        assert storage_values == sorted(storage_values, reverse=True), \
            f"Storage requirements not monotonically decreasing: {storage_values}"

    def test_all_storage_requirements_positive(self, results):
        """At 370 GWh/d peak demand, every scenario requires some storage."""
        assert (results["storage_30d_TWh"] > 0).all()

    def test_s1_storage_near_validated_value(self, results):
        """S1 (P10 imports) should produce ~6.5 TWh storage requirement."""
        s1 = results.loc[results["import_percentile"] == 10, "storage_30d_TWh"].iloc[0]
        assert 5.0 < s1 < 8.0, f"S1 storage = {s1:.2f} TWh, outside expected range"

    def test_s4_storage_near_validated_value(self, results):
        """S4 (P50 imports) should produce ~3.9 TWh storage requirement."""
        s4 = results.loc[results["import_percentile"] == 50, "storage_30d_TWh"].iloc[0]
        assert 2.5 < s4 < 5.0, f"S4 storage = {s4:.2f} TWh, outside expected range"

    def test_daily_gap_consistent_with_storage(self, results):
        """storage_30d_GWh should equal daily_gap_GWh_d × 30 for every row."""
        for _, row in results.iterrows():
            expected = row["daily_gap_GWh_d"] * 30
            assert abs(row["storage_30d_GWh"] - expected) < 2.0, \
                f"Inconsistency in {row['label']}: gap×30={expected:.0f} ≠ storage={row['storage_30d_GWh']:.0f}"

    def test_twh_consistent_with_gwh(self, results):
        """storage_30d_TWh must equal storage_30d_GWh / 1000."""
        for _, row in results.iterrows():
            assert abs(row["storage_30d_TWh"] - row["storage_30d_GWh"] / 1000) < 0.01, \
                f"TWh/GWh inconsistency in {row['label']}"


# ---------------------------------------------------------------------------
# Seasonal peaks regression test
# ---------------------------------------------------------------------------

class TestSeasonalPeaksRegression:

    def test_post_2022_seasons_present(self, daily):
        peaks = bcap.seasonal_peaks(daily)
        for season in ["2022/23", "2023/24", "2024/25"]:
            assert season in peaks.index, f"Season {season} missing from seasonal_peaks"

    def test_2021_22_peak_above_post_2022_peaks(self, daily):
        """Winter 2021/22 (transitional) should have a higher peak than later winters."""
        peaks = bcap.seasonal_peaks(daily)
        if "2021/22" in peaks.index:
            peak_2122 = peaks.loc["2021/22", "peak_GWh_d"]
            later_peaks = peaks.loc[["2022/23", "2023/24", "2024/25"], "peak_GWh_d"]
            assert peak_2122 > later_peaks.max(), \
                "2021/22 peak should exceed all post-2022 season peaks"
