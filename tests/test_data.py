"""
tests/test_data.py — Unit tests for bsd.data using a minimal synthetic CSV.

These tests use a fabricated in-memory CSV so they run without the real data
file and without network access.  They verify:

  - Storage rows are excluded when exclude_storage=True.
  - Rows before the cutoff date are excluded.
  - kWh/d values are correctly divided by 1 000 000 to yield GWh/d.
  - The 'is_winter' flag is set on Nov–Mar rows and cleared on other months.
  - Indicator filtering passes through only the requested indicator.
  - load_daily_imports_by_source returns one row per (date, adjacent system).
  - load_daily_exports filters correctly by domestic_only and exclude_storage.
  - load_demand_proxy merges domestic demand with imports on date.
  - gas_winter_label maps dates to the correct season string.
"""

from io import StringIO

import pandas as pd
import pytest

import bsd.data as bdata


# ---------------------------------------------------------------------------
# Shared synthetic data
# ---------------------------------------------------------------------------

def _make_raw_csv(rows: list[dict]) -> StringIO:
    """Serialise a list of row dicts to an in-memory CSV that mimics the real
    ENTSOG export format (only the columns bsd.data actually reads)."""
    df = pd.DataFrame(rows)
    # The real file has a BOM on the first column; simulate that here.
    csv_text = df.to_csv(index=False)
    # Inject BOM onto the 'id' column name.
    csv_text = "﻿" + csv_text
    return StringIO(csv_text)


def _row(
    date: str,
    adjacent: str,
    indicator: str,
    value_kwh: float,
    direction: str = "entry",
) -> dict:
    """Helper to build a minimal raw-CSV row."""
    return {
        "id": "dummy",
        "dataSet": 1,
        "dataSetLabel": "Aggregates",
        "indicator": indicator,
        "periodType": "day",
        "periodFrom": date,
        "periodTo": date,
        "countryKey": "CZ",
        "countryLabel": "Czechia",
        "bzKey": "CZ---------",
        "bzShort": "Czech",
        "bzLong": "Czech Balancing Zone",
        "operatorKey": "CZ-TSO-0001",
        "operatorLabel": "NET4GAS, s.r.o.",
        "tsoEicCode": "21X000000001304L",
        "directionKey": direction,
        "adjacentSystemsKey": adjacent,
        "adjacentSystemsLabel": adjacent,
        "year": pd.Timestamp(date).year,
        "month": pd.Timestamp(date).month,
        "day": pd.Timestamp(date).day,
        "unit": "kWh/d",
        "value": value_kwh,
        "countPointPresents": 1,
        "flowStatus": "Provisionnal",
        "pointsNames": "dummy",
        "lastUpdateDateTime": "2026-01-01 12:00",
    }


# ---------------------------------------------------------------------------
# Tests: load_daily_imports
# ---------------------------------------------------------------------------

class TestLoadDailyImports:

    def _load(self, rows, **kwargs):
        return bdata.load_daily_imports(_make_raw_csv(rows), **kwargs)

    def test_unit_conversion_kwh_to_gwh(self):
        """1 000 000 kWh/d should appear as 1.0 GWh/d in the output."""
        rows = [_row("2023-01-15", "DE THE BZ", "Physical Flow", 1_000_000)]
        df = self._load(rows, cutoff=pd.Timestamp("2022-01-01"))
        assert df["GWh_d"].iloc[0] == pytest.approx(1.0)

    def test_storage_excluded_by_default(self):
        """Rows with adjacentSystemsLabel == 'Storage' must be dropped."""
        rows = [
            _row("2023-01-15", "Storage", "Physical Flow", 500_000_000),
            _row("2023-01-15", "DE THE BZ", "Physical Flow", 200_000_000),
        ]
        df = self._load(rows, cutoff=pd.Timestamp("2022-01-01"))
        # Only the DE THE BZ row should contribute.
        assert df["GWh_d"].iloc[0] == pytest.approx(200.0)

    def test_storage_included_when_flag_false(self):
        """When exclude_storage=False both rows are summed."""
        rows = [
            _row("2023-01-15", "Storage", "Physical Flow", 500_000_000),
            _row("2023-01-15", "DE THE BZ", "Physical Flow", 200_000_000),
        ]
        df = self._load(rows, cutoff=pd.Timestamp("2022-01-01"), exclude_storage=False)
        assert df["GWh_d"].iloc[0] == pytest.approx(700.0)

    def test_cutoff_excludes_earlier_dates(self):
        """Rows before the cutoff date must be dropped entirely."""
        rows = [
            _row("2021-12-01", "DE THE BZ", "Physical Flow", 100_000_000),
            _row("2022-03-02", "DE THE BZ", "Physical Flow", 200_000_000),
        ]
        df = self._load(rows, cutoff=pd.Timestamp("2022-03-01"))
        assert len(df) == 1
        assert df["GWh_d"].iloc[0] == pytest.approx(200.0)

    def test_indicator_filter_physical_flow(self):
        """Only Physical Flow rows are returned when indicator='Physical Flow'."""
        rows = [
            _row("2023-01-15", "DE THE BZ", "Physical Flow", 300_000_000),
            _row("2023-01-15", "DE THE BZ", "Allocation", 999_000_000),
        ]
        df = self._load(rows, cutoff=pd.Timestamp("2022-01-01"), indicator="Physical Flow")
        assert df["GWh_d"].iloc[0] == pytest.approx(300.0)

    def test_indicator_filter_allocation(self):
        """Only Allocation rows are returned when indicator='Allocation'."""
        rows = [
            _row("2023-01-15", "DE THE BZ", "Physical Flow", 300_000_000),
            _row("2023-01-15", "DE THE BZ", "Allocation", 999_000_000),
        ]
        df = self._load(rows, cutoff=pd.Timestamp("2022-01-01"), indicator="Allocation")
        assert df["GWh_d"].iloc[0] == pytest.approx(999.0)

    def test_multiple_sources_summed_per_day(self):
        """Flows from different adjacent systems on the same day are summed."""
        rows = [
            _row("2023-02-10", "DE THE BZ", "Physical Flow", 100_000_000),
            _row("2023-02-10", "Slovakia", "Physical Flow", 50_000_000),
        ]
        df = self._load(rows, cutoff=pd.Timestamp("2022-01-01"))
        assert len(df) == 1
        assert df["GWh_d"].iloc[0] == pytest.approx(150.0)

    def test_is_winter_flag_set_correctly(self):
        """is_winter should be True for Nov–Mar and False for Apr–Oct."""
        months_and_expected = [
            ("2023-01-15", True),   # January
            ("2023-02-15", True),   # February
            ("2023-03-15", True),   # March
            ("2023-04-15", False),  # April
            ("2023-07-15", False),  # July
            ("2023-11-15", True),   # November
            ("2023-12-15", True),   # December
        ]
        rows = [_row(d, "DE THE BZ", "Physical Flow", 1_000_000) for d, _ in months_and_expected]
        df = self._load(rows, cutoff=pd.Timestamp("2022-01-01")).set_index("date")
        for date_str, expected_winter in months_and_expected:
            ts = pd.Timestamp(date_str)
            assert df.loc[ts, "is_winter"] == expected_winter, \
                f"is_winter wrong for {date_str}"

    def test_output_sorted_by_date(self):
        """Returned DataFrame must be sorted chronologically."""
        rows = [
            _row("2023-03-01", "DE THE BZ", "Physical Flow", 100_000_000),
            _row("2023-01-01", "DE THE BZ", "Physical Flow", 200_000_000),
            _row("2023-02-01", "DE THE BZ", "Physical Flow", 150_000_000),
        ]
        df = self._load(rows, cutoff=pd.Timestamp("2022-01-01"))
        assert list(df["date"]) == sorted(df["date"].tolist())

    def test_empty_result_when_all_filtered(self):
        """If all rows are filtered out an empty DataFrame is returned."""
        rows = [_row("2021-01-01", "DE THE BZ", "Physical Flow", 100_000_000)]
        df = self._load(rows, cutoff=pd.Timestamp("2022-01-01"))
        assert len(df) == 0


# ---------------------------------------------------------------------------
# Tests: load_daily_imports_by_source
# ---------------------------------------------------------------------------

class TestLoadDailyImportsBySource:

    def _load(self, rows, **kwargs):
        return bdata.load_daily_imports_by_source(_make_raw_csv(rows), **kwargs)

    def test_returns_one_row_per_date_source(self):
        """Each (date, adjacent system) combination becomes one row."""
        rows = [
            _row("2023-01-15", "DE THE BZ", "Physical Flow", 200_000_000),
            _row("2023-01-15", "Slovakia",  "Physical Flow",  50_000_000),
            _row("2023-01-16", "DE THE BZ", "Physical Flow", 180_000_000),
        ]
        df = self._load(rows, cutoff=pd.Timestamp("2022-01-01"))
        assert len(df) == 3

    def test_values_converted_to_gwh(self):
        """Values in the by-source frame are also in GWh/d."""
        rows = [_row("2023-01-15", "DE THE BZ", "Physical Flow", 2_000_000)]
        df = self._load(rows, cutoff=pd.Timestamp("2022-01-01"))
        assert df["GWh_d"].iloc[0] == pytest.approx(2.0)


# ---------------------------------------------------------------------------
# Tests: load_daily_exports
# ---------------------------------------------------------------------------

class TestLoadDailyExports:

    def _load(self, rows, **kwargs):
        return bdata.load_daily_exports(_make_raw_csv(rows), **kwargs)

    def _exit_row(self, date, adjacent, value_kwh):
        return _row(date, adjacent, "Physical Flow", value_kwh, direction="exit")

    def test_unit_conversion(self):
        rows = [self._exit_row("2025-01-15", "Distribution", 2_000_000)]
        df = self._load(rows, cutoff=pd.Timestamp("2022-01-01"))
        assert df["GWh_d"].iloc[0] == pytest.approx(2.0)

    def test_storage_excluded_by_default(self):
        rows = [
            self._exit_row("2025-01-15", "Storage", 500_000_000),
            self._exit_row("2025-01-15", "Distribution", 200_000_000),
        ]
        df = self._load(rows, cutoff=pd.Timestamp("2022-01-01"))
        assert df["GWh_d"].iloc[0] == pytest.approx(200.0)

    def test_storage_included_when_flag_false(self):
        rows = [
            self._exit_row("2025-01-15", "Storage", 500_000_000),
            self._exit_row("2025-01-15", "Distribution", 200_000_000),
        ]
        df = self._load(rows, cutoff=pd.Timestamp("2022-01-01"), exclude_storage=False)
        assert df["GWh_d"].iloc[0] == pytest.approx(700.0)

    def test_domestic_only_keeps_distribution_and_final_consumers(self):
        rows = [
            self._exit_row("2025-01-15", "Distribution",    100_000_000),
            self._exit_row("2025-01-15", "Final Consumers",  50_000_000),
            self._exit_row("2025-01-15", "DE THE BZ",       300_000_000),  # transit
            self._exit_row("2025-01-15", "Slovakia",        200_000_000),  # transit
        ]
        df = self._load(rows, cutoff=pd.Timestamp("2022-01-01"), domestic_only=True)
        assert df["GWh_d"].iloc[0] == pytest.approx(150.0)

    def test_domestic_only_excludes_transit(self):
        rows = [
            self._exit_row("2025-01-15", "DE THE BZ", 999_000_000),
        ]
        df = self._load(rows, cutoff=pd.Timestamp("2022-01-01"), domestic_only=True)
        assert len(df) == 0

    def test_cutoff_applied(self):
        rows = [
            self._exit_row("2021-12-01", "Distribution", 100_000_000),
            self._exit_row("2025-01-15", "Distribution", 200_000_000),
        ]
        df = self._load(rows, cutoff=pd.Timestamp("2022-01-01"))
        assert len(df) == 1
        assert df["GWh_d"].iloc[0] == pytest.approx(200.0)

    def test_is_winter_flag(self):
        rows = [
            self._exit_row("2025-01-15", "Distribution", 1_000_000),
            self._exit_row("2025-06-15", "Distribution", 1_000_000),
        ]
        df = self._load(rows, cutoff=pd.Timestamp("2022-01-01")).set_index("date")
        assert df.loc[pd.Timestamp("2025-01-15"), "is_winter"] == True
        assert df.loc[pd.Timestamp("2025-06-15"), "is_winter"] == False


# ---------------------------------------------------------------------------
# Tests: load_demand_proxy
# ---------------------------------------------------------------------------

class TestLoadDemandProxy:

    def _imports_csv(self, rows):
        return _make_raw_csv(rows)

    def _exports_csv(self, rows):
        return _make_raw_csv(rows)

    def test_merges_demand_and_imports_on_date(self):
        imp_rows = [_row("2025-01-15", "DE THE BZ", "Physical Flow", 200_000_000)]
        exp_rows = [_row("2025-01-15", "Distribution", "Physical Flow", 300_000_000,
                         direction="exit")]
        df = bdata.load_demand_proxy(
            self._imports_csv(imp_rows),
            self._exports_csv(exp_rows),
            cutoff=pd.Timestamp("2022-01-01"),
        )
        assert len(df) == 1
        assert df["imports_GWh_d"].iloc[0] == pytest.approx(200.0)
        assert df["demand_GWh_d"].iloc[0] == pytest.approx(300.0)

    def test_inner_join_drops_unmatched_dates(self):
        imp_rows = [
            _row("2025-01-15", "DE THE BZ", "Physical Flow", 200_000_000),
            _row("2025-01-16", "DE THE BZ", "Physical Flow", 180_000_000),
        ]
        exp_rows = [
            _row("2025-01-15", "Distribution", "Physical Flow", 300_000_000,
                 direction="exit"),
            # no export row for Jan 16
        ]
        df = bdata.load_demand_proxy(
            self._imports_csv(imp_rows),
            self._exports_csv(exp_rows),
            cutoff=pd.Timestamp("2022-01-01"),
        )
        assert len(df) == 1
        assert df["date"].iloc[0].date() == pd.Timestamp("2025-01-15").date()

    def test_only_domestic_exits_in_demand(self):
        imp_rows = [_row("2025-01-15", "DE THE BZ", "Physical Flow", 200_000_000)]
        exp_rows = [
            _row("2025-01-15", "Distribution",   "Physical Flow", 100_000_000,
                 direction="exit"),
            _row("2025-01-15", "Final Consumers", "Physical Flow",  50_000_000,
                 direction="exit"),
            _row("2025-01-15", "Slovakia",        "Physical Flow", 999_000_000,
                 direction="exit"),  # transit — must be excluded
        ]
        df = bdata.load_demand_proxy(
            self._imports_csv(imp_rows),
            self._exports_csv(exp_rows),
            cutoff=pd.Timestamp("2022-01-01"),
        )
        assert df["demand_GWh_d"].iloc[0] == pytest.approx(150.0)


# ---------------------------------------------------------------------------
# Tests: gas_winter_label
# ---------------------------------------------------------------------------

class TestGasWinterLabel:

    def _label(self, dates: list[str]) -> list:
        s = pd.Series(pd.to_datetime(dates))
        return bdata.gas_winter_label(s).tolist()

    def test_november_maps_to_current_slash_next(self):
        assert self._label(["2023-11-01"]) == ["2023/24"]

    def test_december_maps_to_current_slash_next(self):
        assert self._label(["2023-12-31"]) == ["2023/24"]

    def test_january_maps_to_prev_slash_current(self):
        assert self._label(["2024-01-15"]) == ["2023/24"]

    def test_march_maps_to_prev_slash_current(self):
        assert self._label(["2024-03-31"]) == ["2023/24"]

    def test_april_is_nan(self):
        result = self._label(["2024-04-01"])
        assert pd.isna(result[0])

    def test_october_is_nan(self):
        result = self._label(["2024-10-31"])
        assert pd.isna(result[0])

    def test_multiple_seasons(self):
        labels = self._label(["2022-12-01", "2023-02-01", "2023-11-01", "2024-01-01"])
        assert labels == ["2022/23", "2022/23", "2023/24", "2023/24"]
