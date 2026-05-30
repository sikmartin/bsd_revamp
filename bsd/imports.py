"""Import-capacity computations: scenario percentiles and P99 cold-day benchmarks."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .constants import MONTH_ORDER, MONTH_NAMES, COLD_DAY_QUANTILE
from .data import DATA_PATH_IMPORTS, DATA_PATH_STORAGE_GIE, DEFAULT_CUTOFF, load_daily_imports, WINTER_MONTHS


def compute_monthly_imports(
    scenarios: dict,
    *,
    imports_path: str | Path = DATA_PATH_IMPORTS,
    cutoff: str | None = DEFAULT_CUTOFF,
    month_order: list[int] = MONTH_ORDER,
) -> dict[str, pd.Series]:
    """Compute month-specific import percentiles for each scenario.

    Parameters
    ----------
    scenarios:
        Dict mapping scenario key → object with a ``percentile`` attribute
        (int, 0–100).  Compatible with ``Scenario`` dataclass and plain dicts
        like ``{"S1": {"percentile": 10}}``.

    Returns
    -------
    Dict mapping scenario key → pd.Series indexed by month_num (GWh/d).
    """
    daily = load_daily_imports(imports_path, cutoff=cutoff)
    winter = daily[daily["month"].isin(month_order)].copy()

    result: dict[str, pd.Series] = {}
    for key, sc in scenarios.items():
        pct = sc.percentile if hasattr(sc, "percentile") else sc["percentile"]
        result[key] = pd.Series(
            {m: winter[winter["month"] == m]["GWh_d"].quantile(pct / 100)
             for m in month_order}
        )
    return result


def compute_p99_imports(
    *,
    imports_path: str | Path = DATA_PATH_IMPORTS,
    gio_path: str | Path = DATA_PATH_STORAGE_GIE,
    cutoff: str | None = DEFAULT_CUTOFF,
    month_order: list[int] = MONTH_ORDER,
    cold_day_quantile: float = COLD_DAY_QUANTILE,
) -> tuple[pd.Series, pd.Series]:
    """Compute P99 import benchmarks: cold-day conditional and unconditional.

    Cold days are defined as days in the top ``cold_day_quantile`` of
    storage-withdrawal magnitude within each month (post-``cutoff`` winters).

    Returns
    -------
    (p99_cold, p99_unconditional) — each a pd.Series indexed by month_num (GWh/d).
    """
    daily = load_daily_imports(imports_path, cutoff=cutoff)
    winter = daily[daily["month"].isin(month_order)].copy()

    sto_raw = pd.read_csv(
        gio_path, sep=";",
        parse_dates=["Gas Day Start (status at 6AM  CEST)"],
    )
    sto_raw.columns = sto_raw.columns.str.strip()
    sto_raw = sto_raw.rename(columns={
        "Gas Day Start (status at 6AM  CEST)": "date",
        "Withdrawal (GWh/d)": "withdrawal",
    })
    sto_raw["date_key"] = pd.to_datetime(sto_raw["date"]).dt.normalize()

    merged = winter.copy()
    merged["date_key"] = merged["date"].dt.normalize()
    merged = merged.merge(
        sto_raw[["date_key", "withdrawal"]].dropna(),
        on="date_key", how="inner",
    )

    cold_mask = pd.Series(False, index=merged.index)
    for m in month_order:
        mask = merged["month"] == m
        thresh = merged.loc[mask, "withdrawal"].quantile(cold_day_quantile)
        cold_mask = cold_mask | (mask & (merged["withdrawal"] >= thresh))

    p99_cold = pd.Series(
        {m: merged.loc[(merged["month"] == m) & cold_mask, "GWh_d"].quantile(0.99)
         for m in month_order}
    )
    p99_uncond = pd.Series(
        {m: merged[merged["month"] == m]["GWh_d"].quantile(0.99)
         for m in month_order}
    )
    return p99_cold, p99_uncond


def import_table(
    monthly_imports: dict[str, pd.Series],
    p99_cold: pd.Series | None = None,
    p99_uncond: pd.Series | None = None,
    *,
    month_names: dict[int, str] | None = None,
) -> pd.DataFrame:
    """Format scenario import percentiles alongside P99 benchmarks as a display table."""
    names = month_names or MONTH_NAMES
    df = pd.DataFrame(monthly_imports).round(1)
    df.index = [names[m] for m in df.index]
    if p99_uncond is not None:
        df["P99 unconditional"] = p99_uncond.values.round(1)
    if p99_cold is not None:
        df["P99 cold days"] = p99_cold.values.round(1)
    return df
