"""Demand-profile loading for the Czech balancing zone stress models."""

from pathlib import Path
from typing import NamedTuple

import pandas as pd

from .constants import MONTH_ORDER, MONTH_NUM, STRESS_PEAK_DAYS, STRESS_RESIDUAL_DAYS
from .data import DATA_PATH_DEMAND_PEAK, DATA_PATH_DEMAND_30DAY


class DemandProfile(NamedTuple):
    """Per-month demand Series, all indexed by integer month number (1–12)."""

    peak: pd.Series  # 1-in-20 peak-day demand, GWh/d (R.max.den)
    residual: pd.Series  # residual average for days 8–30, GWh/d
    total: pd.Series  # 30-day total demand, GWh (r_30dnu)


def load_demand_profile(
    peak_path: str | Path = DATA_PATH_DEMAND_PEAK,
    r30_path: str | Path = DATA_PATH_DEMAND_30DAY,
    *,
    month_order: list[int] = MONTH_ORDER,
    stress_peak_days: int = STRESS_PEAK_DAYS,
    stress_residual_days: int = STRESS_RESIDUAL_DAYS,
) -> DemandProfile:
    """Load and compute the two-tier demand profile used in both branches.

    Returns peak (GWh/d), residual (GWh/d), and 30-day total (GWh),
    each as a pd.Series indexed by integer month number.
    """
    peak_raw = pd.read_csv(peak_path)
    peak_raw.columns = peak_raw.columns.str.strip()
    peak_raw["month_num"] = peak_raw["month"].str.lower().map(MONTH_NUM)
    peak_raw["peak_GWh_d"] = peak_raw["value [mhw]"] / 1000
    peak = peak_raw.set_index("month_num")["peak_GWh_d"].reindex(month_order)

    r30_raw = pd.read_csv(r30_path)
    r30_raw.columns = r30_raw.columns.str.strip()
    r30_raw["month_num"] = r30_raw["month"].str.lower().map(MONTH_NUM)
    r30_raw["total_GWh"] = r30_raw["value [mhw]"] / 1000
    total = r30_raw.set_index("month_num")["total_GWh"].reindex(month_order)

    residual = (total - stress_peak_days * peak) / stress_residual_days

    return DemandProfile(peak=peak, residual=residual, total=total)


def demand_profile_table(
    profile: DemandProfile, month_names: dict[int, str] | None = None
) -> pd.DataFrame:
    """Format the demand profile as a display DataFrame."""
    from .constants import MONTH_NAMES

    names = month_names or MONTH_NAMES
    return pd.DataFrame(
        {
            "Peak 7d (GWh/d)": profile.peak.round(1),
            "Residual 23d (GWh/d)": profile.residual.round(1),
            "Total 30d (GWh)": profile.total.round(0),
        }
    ).rename(index=names)
