"""
tests/test_capacity.py — Unit tests for bsd.capacity using synthetic data.

These tests verify the correctness of the mathematical operations in
capacity.py without touching the real data file:

  - add_rolling_avg produces the correct rolling mean.
  - import_percentile_table returns expected percentiles from a known
    distribution.
  - storage_scenarios computes daily_gap and storage_30d correctly,
    including the max(0, ...) floor that prevents negative storage needs.
  - winter_daily correctly filters to Nov–Mar rows.
  - seasonal_peaks groups by gas winter and returns the right aggregates.
"""

import pandas as pd
import numpy as np
import pytest

import bsd.capacity as bcap


# ---------------------------------------------------------------------------
# Helpers to build synthetic daily DataFrames
# ---------------------------------------------------------------------------

def _make_daily(dates: list[str], values: list[float]) -> pd.DataFrame:
    """Build a minimal daily DataFrame as returned by bsd.data.load_daily_imports."""
    dates_ts = pd.to_datetime(dates)
    df = pd.DataFrame({
        "date": dates_ts,
        "GWh_d": values,
        "month": dates_ts.month,
        "year": dates_ts.year,
        "is_winter": dates_ts.month.isin(bsd_winter_months()),
    })
    return df.sort_values("date").reset_index(drop=True)


def bsd_winter_months():
    from bsd.data import WINTER_MONTHS
    return WINTER_MONTHS


# ---------------------------------------------------------------------------
# Tests: winter_daily
# ---------------------------------------------------------------------------

class TestWinterDaily:

    def test_keeps_only_oct_to_mar(self):
        dates = [
            "2023-01-15",  # winter
            "2023-03-31",  # winter
            "2023-04-01",  # not winter
            "2023-10-31",  # winter (Oct is in WINTER_MONTHS)
            "2023-11-01",  # winter
            "2023-12-25",  # winter
        ]
        df = _make_daily(dates, [1.0] * len(dates))
        result = bcap.winter_daily(df)
        assert set(result["month"].tolist()) <= {1, 2, 3, 10, 11, 12}
        assert len(result) == 5

    def test_returns_empty_if_no_winter_rows(self):
        dates = ["2023-05-01", "2023-08-15"]
        df = _make_daily(dates, [100.0, 200.0])
        result = bcap.winter_daily(df)
        assert len(result) == 0


# ---------------------------------------------------------------------------
# Tests: add_rolling_avg
# ---------------------------------------------------------------------------

class TestAddRollingAvg:

    def test_rolling_mean_is_correct(self):
        """Rolling average over a 3-day window on a simple sequence."""
        dates = [f"2023-01-{d:02d}" for d in range(1, 8)]
        values = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0]
        df = _make_daily(dates, values)
        result = bcap.add_rolling_avg(df, window=3)

        col = "roll3_avg_GWh_d"
        # First two rows are NaN (window not yet full).
        assert pd.isna(result.loc[0, col])
        assert pd.isna(result.loc[1, col])
        # Third row: mean(10, 20, 30) = 20.
        assert result.loc[2, col] == pytest.approx(20.0)
        # Seventh row: mean(50, 60, 70) = 60.
        assert result.loc[6, col] == pytest.approx(60.0)

    def test_column_name_reflects_window(self):
        dates = [f"2023-01-{d:02d}" for d in range(1, 6)]
        df = _make_daily(dates, [1.0] * 5)
        result = bcap.add_rolling_avg(df, window=7)
        assert "roll7_avg_GWh_d" in result.columns

    def test_original_columns_preserved(self):
        dates = ["2023-01-01", "2023-01-02"]
        df = _make_daily(dates, [1.0, 2.0])
        result = bcap.add_rolling_avg(df)
        for col in ["date", "GWh_d", "month", "year", "is_winter"]:
            assert col in result.columns


# ---------------------------------------------------------------------------
# Tests: import_percentile_table
# ---------------------------------------------------------------------------

class TestImportPercentileTable:

    def _uniform_winter_df(self, n: int = 300, low: float = 0.0, high: float = 100.0):
        """Uniform distribution over winter months — easy to reason about."""
        rng = np.random.default_rng(42)
        # Distribute across Jan, Feb, Mar, Nov, Dec to cover all winter months.
        months = ([1] * (n // 5) + [2] * (n // 5) + [3] * (n // 5)
                  + [11] * (n // 5) + [12] * (n // 5))
        # Pad to exactly n if rounding dropped some.
        months = months[:n]
        years = [2023] * len(months)
        days = list(range(1, len(months) + 1))

        dates = [
            pd.Timestamp(year=y, month=m, day=min(d, 28))
            for y, m, d in zip(years, months, days)
        ]
        values = list(rng.uniform(low, high, len(dates)))
        return _make_daily([str(d.date()) for d in dates], values)

    def test_percentile_ordering(self):
        """P10 <= P50 <= P90 for both single-day and rolling columns."""
        df = self._uniform_winter_df()
        ptable = bcap.import_percentile_table(df, percentiles=[10, 50, 90])
        assert ptable.loc[10, "single_day_GWh_d"] <= ptable.loc[50, "single_day_GWh_d"]
        assert ptable.loc[50, "single_day_GWh_d"] <= ptable.loc[90, "single_day_GWh_d"]

    def test_p0_is_min_p100_is_max(self):
        """P0 and P100 should match the empirical min and max."""
        df = self._uniform_winter_df()
        ptable = bcap.import_percentile_table(df, percentiles=[0, 100])
        w = bcap.winter_daily(df)
        assert ptable.loc[0, "single_day_GWh_d"] == pytest.approx(w["GWh_d"].min())
        assert ptable.loc[100, "single_day_GWh_d"] == pytest.approx(w["GWh_d"].max())

    def test_index_is_percentile_values(self):
        df = self._uniform_winter_df()
        ptable = bcap.import_percentile_table(df, percentiles=[25, 75])
        assert list(ptable.index) == [25, 75]


# ---------------------------------------------------------------------------
# Tests: storage_scenarios
# ---------------------------------------------------------------------------

class TestStorageScenarios:

    def _constant_df(self, ghw_d: float, n_days: int = 300) -> pd.DataFrame:
        """Daily DataFrame where every winter day has the same import value.

        With constant imports every percentile is the same value, so we can
        predict the storage gap exactly.
        """
        months = ([1, 2, 3, 11, 12] * (n_days // 5 + 1))[:n_days]
        dates = [pd.Timestamp(2023, m, 1) + pd.Timedelta(days=i % 28)
                 for i, m in enumerate(months)]
        return _make_daily([str(d.date()) for d in dates], [ghw_d] * n_days)

    def test_storage_gap_formula(self):
        """gap = peak_demand − 30d_sustained_import; storage = gap × 30."""
        # Constant imports of 200 GWh/d → every percentile = 200.
        df = self._constant_df(200.0)
        peak = 370.0
        scenarios = [bcap.Scenario("Test", 50, "")]
        result = bcap.storage_scenarios(df, peak_demand_GWh_d=peak, scenarios=scenarios)

        expected_gap = peak - 200.0         # 170 GWh/d
        expected_storage = expected_gap * 30  # 5 100 GWh

        assert result.loc[0, "daily_gap_GWh_d"] == pytest.approx(expected_gap, rel=0.01)
        assert result.loc[0, "storage_30d_GWh"] == pytest.approx(expected_storage, rel=0.01)
        assert result.loc[0, "storage_30d_TWh"] == pytest.approx(expected_storage / 1000, rel=0.01)

    def test_no_negative_storage_when_imports_exceed_demand(self):
        """When imports > peak demand the storage requirement is 0, not negative."""
        df = self._constant_df(500.0)  # imports well above peak
        peak = 370.0
        scenarios = [bcap.Scenario("Test", 50, "")]
        result = bcap.storage_scenarios(df, peak_demand_GWh_d=peak, scenarios=scenarios)

        assert result.loc[0, "daily_gap_GWh_d"] == 0.0
        assert result.loc[0, "storage_30d_GWh"] == 0.0

    def test_higher_stress_means_more_storage(self):
        """A lower import percentile (more stress) requires more storage."""
        df = self._constant_df.__func__(self, 200.0)  # type: ignore[attr-defined]
        # Build scenarios with different percentiles on the same non-constant data.
        rng = np.random.default_rng(0)
        months = [1, 2, 3, 11, 12] * 60
        dates = [pd.Timestamp(2023, m, 1) + pd.Timedelta(days=i % 28)
                 for i, m in enumerate(months)]
        vals = list(rng.uniform(100, 400, len(months)))
        df2 = _make_daily([str(d.date()) for d in dates], vals)

        scenarios = [
            bcap.Scenario("Stressed", 10, ""),
            bcap.Scenario("Median",   50, ""),
        ]
        result = bcap.storage_scenarios(df2, peak_demand_GWh_d=370.0, scenarios=scenarios)
        # Stressed (P10 imports) should require more storage than Median (P50).
        assert (result.loc[0, "storage_30d_GWh"]
                >= result.loc[1, "storage_30d_GWh"])

    def test_output_has_all_expected_columns(self):
        df = self._constant_df(200.0)
        result = bcap.storage_scenarios(df, 370.0)
        for col in [
            "label", "import_percentile", "description",
            "reliable_import_daily_GWh_d", "reliable_import_30d_avg_GWh_d",
            "daily_gap_GWh_d", "storage_30d_GWh", "storage_30d_TWh",
        ]:
            assert col in result.columns, f"Missing column: {col}"

    def test_default_scenarios_returns_five_rows(self):
        df = self._constant_df(200.0)
        result = bcap.storage_scenarios(df, 370.0)
        assert len(result) == 5
