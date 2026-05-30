"""Branch 1 — Monthly storage obligations (EU Regulation 2017/1938 Art. 6).

Each month is a standalone 30-day stress test: 7 peak days at R.max.den,
23 residual days at (r_30dnu − 7·R.max.den)/23.  Bisection finds the minimum
1-Oct/1-Nov/.../1-Mar fill that keeps the simulation feasible.
"""

from __future__ import annotations

from typing import Callable

import pandas as pd

from .constants import (
    CAPACITY_TWH, STRESS_PEAK_DAYS, STRESS_RESIDUAL_DAYS, MONTH_NAMES,
)


def simulate_month(
    start_fill_pct: float,
    month: int,
    imp_GWh_d: float,
    wc_func: Callable[[float], float],
    peak_demand: pd.Series,
    residual_demand: pd.Series,
    *,
    capacity_TWh: float = CAPACITY_TWH,
) -> dict:
    """Simulate the 30-day Art. 6 stress event for one calendar month.

    Parameters
    ----------
    start_fill_pct:
        Starting fill level (0–100 %).
    month:
        Integer month number (1–12).
    imp_GWh_d:
        Constant import level for the 30-day period (GWh/d).
    wc_func:
        Withdrawal-capacity callable: fill_pct → max deliverable GWh/d.
    peak_demand:
        pd.Series indexed by month_num; 1-in-20 peak-day demand (GWh/d).
    residual_demand:
        pd.Series indexed by month_num; residual 23-day average (GWh/d).
    capacity_TWh:
        Total working-gas capacity (TWh).

    Returns
    -------
    dict with keys: feasible (bool), binding (str|None), day (int|None),
    fill_end (float), fill_trajectory (list[float]).
    """
    gap_peak  = max(0.0, float(peak_demand[month])    - imp_GWh_d)
    gap_resid = max(0.0, float(residual_demand[month]) - imp_GWh_d)
    gaps = [gap_peak] * STRESS_PEAK_DAYS + [gap_resid] * STRESS_RESIDUAL_DAYS

    fill = float(start_fill_pct)
    delta = 100.0 / (capacity_TWh * 1000)  # % points per GWh withdrawn
    traj = [fill]

    for t, g in enumerate(gaps):
        if wc_func(fill) < g - 1e-9:
            return {"feasible": False, "binding": "withdrawal rate",
                    "day": t, "fill_end": fill, "fill_trajectory": traj}
        fill -= g * delta
        if fill < -1e-9:
            return {"feasible": False, "binding": "volume",
                    "day": t, "fill_end": fill, "fill_trajectory": traj}
        traj.append(fill)

    return {"feasible": True, "binding": None,
            "day": None, "fill_end": fill, "fill_trajectory": traj}


def min_start_fill_month(
    month: int,
    imp_GWh_d: float,
    wc_func: Callable[[float], float],
    peak_demand: pd.Series,
    residual_demand: pd.Series,
    *,
    capacity_TWh: float = CAPACITY_TWH,
    tol: float = 0.01,
    lo: float = 0.0,
    hi: float = 100.0,
) -> float | None:
    """Bisect for the minimum feasible starting fill (%) for one month.

    Returns ``None`` if infeasible even at ``hi`` (100% fill).
    Returns ``lo`` (0.0) if already feasible with no gas.
    """
    def _sim(fp: float) -> bool:
        return simulate_month(
            fp, month, imp_GWh_d, wc_func, peak_demand, residual_demand,
            capacity_TWh=capacity_TWh,
        )["feasible"]

    if not _sim(hi):
        return None
    if _sim(lo):
        return lo
    while hi - lo > tol:
        mid = (lo + hi) / 2
        if _sim(mid):
            hi = mid
        else:
            lo = mid
    return hi


def run_all_months(
    monthly_imports: dict[str, pd.Series],
    wc_func: Callable[[float], float],
    peak_demand: pd.Series,
    residual_demand: pd.Series,
    scenarios: dict,
    *,
    capacity_TWh: float = CAPACITY_TWH,
    month_order: list[int] | None = None,
) -> dict:
    """Run monthly obligations for all scenarios and months.

    Returns nested dict: results[scenario_key][month] = {start_fill_pct,
    start_fill_TWh, binding, fill_end, sim}.
    """
    from .constants import MONTH_ORDER
    mo = month_order or MONTH_ORDER

    results: dict = {}
    for key in scenarios:
        results[key] = {}
        for m in mo:
            imp = float(monthly_imports[key][m])
            f = min_start_fill_month(
                m, imp, wc_func, peak_demand, residual_demand,
                capacity_TWh=capacity_TWh,
            )
            sim = simulate_month(
                f if f is not None else 100.0,
                m, imp, wc_func, peak_demand, residual_demand,
                capacity_TWh=capacity_TWh,
            )
            # Determine binding constraint by probing just below the minimum fill
            if f is None:
                binding = "infeasible at 100%"
            else:
                probe = simulate_month(
                    max(0.0, f - 0.05), m, imp, wc_func, peak_demand, residual_demand,
                    capacity_TWh=capacity_TWh,
                )
                binding = probe["binding"] or "volume"
            results[key][m] = {
                "start_fill_pct": f,
                "start_fill_TWh": None if f is None else round(f * capacity_TWh / 100, 2),
                "binding": binding,
                "fill_end": sim["fill_end"],
                "sim": sim,
            }
    return results


def obligations_table(
    results: dict,
    scenarios: dict,
    *,
    month_order: list[int] | None = None,
    month_names: dict[int, str] | None = None,
) -> pd.DataFrame:
    """Format obligations as a TWh DataFrame (months × scenarios)."""
    from .constants import MONTH_ORDER
    mo = month_order or MONTH_ORDER
    mn = month_names or MONTH_NAMES
    df = pd.DataFrame(
        {key: {mn[m]: results[key][m]["start_fill_TWh"] for m in mo}
         for key in scenarios}
    )
    sc_labels = {k: (v.label if hasattr(v, "label") else v["label"]) for k, v in scenarios.items()}
    df.columns = [sc_labels[k] for k in scenarios]
    return df
