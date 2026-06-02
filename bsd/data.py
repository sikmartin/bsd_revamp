"""
data.py — Load and clean ENTSOG Transparency Platform aggregate export files.

The raw CSV exported from ENTSOG contains one row per (date, entry point,
indicator) combination.  This module converts that wide, messy format into
clean DataFrames consumed by the rest of the package:

  * load_daily_imports(path, ...)        — total daily entry flows into the
                                           Czech balancing zone, one row per
                                           gas day.
  * load_daily_imports_by_source(path)   — same, split by adjacent system
                                           (corridor-level analysis).
  * load_daily_exports(path, ...)        — total daily exit flows from the
                                           Czech balancing zone; supports
                                           domestic-only filtering for demand
                                           proxy construction.
  * load_demand_proxy(imports, exports)  — daily domestic demand proxy
                                           (Distribution + Final Consumers
                                           exit flows) merged with imports;
                                           used for demand/import correlation
                                           analysis.

Design notes
------------
- All values are converted from kWh/d to GWh/d at load time so downstream
  code never has to think about units.
- The structural break caused by Russia's invasion of Ukraine (Feb 2022)
  dramatically changed Czech import patterns.  A `cutoff` parameter lets
  callers restrict to the post-break period, which is the default.
- Storage entry points are excluded by default because they represent
  withdrawal from/injection into Czech UGS facilities, not cross-border flows.
- The export file (exit direction) covers from March 2022 onwards, but the
  domestic exit points (``Distribution`` and ``Final Consumers``) are only
  populated from January 2025.  The demand proxy is therefore limited to that
  narrower window for correlation analysis.
"""

from pathlib import Path

import pandas as pd

from .constants import WINTER_MONTHS, GAS_STORAGE_LEVY_START, GAS_STORAGE_LEVY_END

# ---------------------------------------------------------------------------
# Public constants
# ---------------------------------------------------------------------------

#: Path to ENTSOG aggregated import data for the Czech balancing zone.
DATA_PATH_IMPORTS = Path("data/cz_gas_imports_2020-2026.csv")

#: Path to ENTSOG aggregated export data for the Czech balancing zone.
DATA_PATH_EXPORTS = Path("data/cz_gas_exports_2020-2026.csv")

#: Path to month-specific 1-in-20 peak demand data (MWh/d).
DATA_PATH_DEMAND_PEAK = Path("data/r_max_den_2025-2026.csv")

#: Path to month-specific 30-day total demand data (MWh).
DATA_PATH_DEMAND_30DAY = Path("data/r_30dnu_2025-2026.csv")

#: Path to GIE storage fill-level time series (2011–present).
DATA_PATH_STORAGE_GIE = Path("data/StorageData_GIE_2011-01-01_2026-05-28.csv")

#: Path to the ENTSOG winter outlooks and rewiews withdrawal and injection curvea
# https://www.entsog.eu/outlooks-reviews#winter-outlooks-and-reviews
DATA_PATH_WTHDRW_CURVE = Path("data/cz_usg_withdrawal_curve_2025.csv")
DATA_PATH_INJCTN_CURVE = Path("data/cz_usg_injection_curve_2025.csv")


#: Default structural-break cutoff.  Pre-2022 data reflects Russian transit
#: volumes and commercial behaviours that are no longer representative.
DEFAULT_CUTOFF = pd.Timestamp("2022-03-01")

#: Adjacent-system label used for domestic storage withdrawal flows.
STORAGE_LABEL = "Storage"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _read_raw(path: str | Path) -> pd.DataFrame:
    """Read the raw ENTSOG export CSV and do minimal normalisation.

    The file uses a BOM (byte-order mark) on the first column name, which
    pandas does not strip automatically with the default engine.  We handle
    that here so callers never see the artefact.
    """
    df = pd.read_csv(path, low_memory=False)

    # Strip BOM from column names if present (common in ENTSOG exports).
    df.columns = [c.lstrip("﻿") for c in df.columns]

    # Parse the period start as a timezone-naive datetime for simplicity.
    # The raw field looks like "2022-01-01 06:00" (CET gas-day boundary).
    df["date"] = pd.to_datetime(df["periodFrom"], utc=False)

    return df


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_daily_imports(
    path: str | Path,
    indicator: str = "Physical Flow",
    cutoff: pd.Timestamp = DEFAULT_CUTOFF,
    exclude_storage: bool = True,
) -> pd.DataFrame:
    """Return total daily entry flows into the Czech balancing zone.

    Each row represents one gas day (identified by the CET 06:00 boundary
    used by NET4GAS / ENTSOG).  The value column ``GWh_d`` is the sum of
    flows across all included entry points.

    Parameters
    ----------
    path:
        Path to the raw ENTSOG aggregate CSV export.
    indicator:
        ``"Physical Flow"`` (default) or ``"Allocation"``.  Physical Flows
        are preferred for capacity reliability analysis because they record
        what actually crossed the border under real operating conditions.
        See analysis notebook Section 2 for the full rationale.
    cutoff:
        Drop all rows with ``date < cutoff``.  Defaults to 2022-03-01 to
        exclude the Russian-transit era.
    exclude_storage:
        If ``True`` (default), drop rows whose ``adjacentSystemsLabel`` is
        ``"Storage"``.  Storage withdrawal is domestic, not an import.

    Returns
    -------
    pd.DataFrame
        Columns: ``date`` (datetime), ``GWh_d`` (float), ``month`` (int),
        ``year`` (int), ``is_winter`` (bool).
    """
    df = _read_raw(path)

    # Filter to the requested indicator and time window.
    mask = (df["indicator"] == indicator) & (df["date"] >= cutoff)
    if exclude_storage:
        mask &= df["adjacentSystemsLabel"] != STORAGE_LABEL

    filtered = df[mask]

    # Aggregate all entry points into a single daily total.
    daily = filtered.groupby("date")["value"].sum().rename("GWh_d").reset_index()

    # Convert kWh/d → GWh/d.
    daily["GWh_d"] = daily["GWh_d"] / 1_000_000

    # Convenience columns used throughout the package.
    daily["month"] = daily["date"].dt.month
    daily["year"] = daily["date"].dt.year
    daily["is_winter"] = daily["month"].isin(WINTER_MONTHS)

    # German import levy; see bsd.constants.
    daily["levy_in_force"] = (daily["date"] >= pd.Timestamp(GAS_STORAGE_LEVY_START)) & (
        daily["date"] <= pd.Timestamp(GAS_STORAGE_LEVY_END)
    )

    return daily.sort_values("date").reset_index(drop=True)


def load_daily_imports_by_source(
    path: str | Path,
    indicator: str = "Physical Flow",
    cutoff: pd.Timestamp = DEFAULT_CUTOFF,
    exclude_storage: bool = True,
) -> pd.DataFrame:
    """Return daily entry flows broken down by adjacent system (corridor).

    The returned DataFrame is in long format:
    ``date | adjacentSystemsLabel | GWh_d | month | year | is_winter``

    This is useful for understanding which corridors are active on
    high-import vs. low-import days, and for corridor-level stress tests.
    """
    df = _read_raw(path)

    mask = (df["indicator"] == indicator) & (df["date"] >= cutoff)
    if exclude_storage:
        mask &= df["adjacentSystemsLabel"] != STORAGE_LABEL

    filtered = df[mask]

    by_source = (
        filtered.groupby(["date", "adjacentSystemsLabel"])["value"]
        .sum()
        .rename("GWh_d")
        .reset_index()
    )

    by_source["GWh_d"] = by_source["GWh_d"] / 1_000_000
    by_source["month"] = by_source["date"].dt.month
    by_source["year"] = by_source["date"].dt.year
    by_source["is_winter"] = by_source["month"].isin(WINTER_MONTHS)

    return by_source.sort_values(["date", "adjacentSystemsLabel"]).reset_index(
        drop=True
    )


def load_daily_exports(
    path: str | Path,
    indicator: str = "Physical Flow",
    cutoff: pd.Timestamp = DEFAULT_CUTOFF,
    exclude_storage: bool = True,
    domestic_only: bool = False,
) -> pd.DataFrame:
    """Return total daily exit flows from the Czech balancing zone.

    Parameters
    ----------
    path:
        Path to the raw ENTSOG aggregate CSV export (exit direction).
    indicator:
        ``"Physical Flow"`` (default) or ``"Allocation"``.
    cutoff:
        Drop all rows with ``date < cutoff``.
    exclude_storage:
        If ``True`` (default), drop rows whose ``adjacentSystemsLabel`` is
        ``"Storage"`` (injections into UGS are not cross-border exports).
    domestic_only:
        If ``True``, keep only ``"Distribution"`` and ``"Final Consumers"``
        rows — i.e. the domestic demand proxy.  Useful for the demand/import
        correlation analysis.  Overrides ``exclude_storage``.

    Returns
    -------
    pd.DataFrame
        Columns: ``date``, ``GWh_d``, ``month``, ``year``, ``is_winter``.
    """
    df = _read_raw(path)

    mask = (df["indicator"] == indicator) & (df["date"] >= cutoff)
    if domestic_only:
        mask &= df["adjacentSystemsLabel"].isin({"Distribution", "Final Consumers"})
    elif exclude_storage:
        mask &= df["adjacentSystemsLabel"] != STORAGE_LABEL

    filtered = df[mask]

    daily = filtered.groupby("date")["value"].sum().rename("GWh_d").reset_index()

    daily["GWh_d"] = daily["GWh_d"] / 1_000_000

    daily["month"] = daily["date"].dt.month
    daily["year"] = daily["date"].dt.year
    daily["is_winter"] = daily["month"].isin(WINTER_MONTHS)

    return daily.sort_values("date").reset_index(drop=True)


def load_demand_proxy(
    imports_path: str | Path,
    exports_path: str | Path,
    indicator: str = "Physical Flow",
    cutoff: pd.Timestamp = DEFAULT_CUTOFF,
) -> pd.DataFrame:
    """Return a merged DataFrame of daily domestic demand and total imports.

    Joins the domestic-only exit flows (``Distribution`` + ``Final Consumers``)
    with total entry flows on ``date``, keeping only days present in both
    series (inner join).  Intended for demand/import correlation analysis.

    Note: the distribution category may exclude some very large industrial
    consumers connected directly to the transmission system; coverage is
    nonetheless sufficient for percentile-level correlation tests.

    Returns
    -------
    pd.DataFrame
        Columns: ``date``, ``demand_GWh_d``, ``imports_GWh_d``,
        ``month``, ``year``, ``is_winter``.
    """
    demand = load_daily_exports(
        exports_path, indicator=indicator, cutoff=cutoff, domestic_only=True
    ).rename(columns={"GWh_d": "demand_GWh_d"})

    imports = load_daily_imports(
        imports_path, indicator=indicator, cutoff=cutoff
    ).rename(columns={"GWh_d": "imports_GWh_d"})

    merged = demand.merge(imports[["date", "imports_GWh_d"]], on="date", how="inner")

    return merged


def load_storage_gie(
    path: str | Path,
    cutoff: pd.Timestamp | str | None = DEFAULT_CUTOFF,
) -> pd.DataFrame:
    """Return daily GIE storage data for the Czech balancing zone.

    Parses the semicolon-separated GIE AGSI+ CSV and returns a clean DataFrame
    with standardised column names.

    Returns
    -------
    pd.DataFrame
        Columns: ``date``, ``fill_pct``, ``withdrawal``, ``wc_declared``.
        Rows with any NaN in those columns are dropped.  Filtered to
        ``date >= cutoff``.
    """
    raw = pd.read_csv(
        path,
        sep=";",
        parse_dates=["Gas Day Start (status at 6AM  CEST)"],
        dayfirst=False,
        decimal=".",
    )
    raw.columns = raw.columns.str.strip()
    raw = raw.rename(
        columns={
            "Gas Day Start (status at 6AM  CEST)": "date",
            "Full (%)": "fill_pct",
            "Withdrawal (GWh/d)": "withdrawal",
            "Withdrawal capacity (GWh/d)": "wc_declared",
        }
    )
    sto = raw[["date", "fill_pct", "withdrawal", "wc_declared"]].dropna()
    if cutoff is not None:
        sto = sto[sto["date"] >= cutoff]
    return sto.reset_index(drop=True)


def gas_winter_label(date_series: pd.Series) -> pd.Series:
    """Map a datetime Series to gas-winter season labels (e.g. '2024/25').

    A gas winter runs from November of year Y through March of year Y+1.
    Days outside Nov–Mar are labelled ``NaN``.
    """
    month = date_series.dt.month
    year = date_series.dt.year

    label = pd.Series(index=date_series.index, dtype="object")
    nov_dec = month.isin([11, 12])
    jan_mar = month.isin([1, 2, 3])

    label[nov_dec] = (
        year[nov_dec].astype(str) + "/" + (year[nov_dec] + 1).astype(str).str[2:]
    )
    label[jan_mar] = (
        (year[jan_mar] - 1).astype(str) + "/" + year[jan_mar].astype(str).str[2:]
    )

    return label
