"""Branch 2 — Season-long storage fill target (1-October minimum fill).

A daily draw-down simulation runs Oct 1 → Mar 31.  Each day uses the full
1-in-20 peak-day demand for that month (no 7+23 split — the season-long stress
applies peak demand every day).  Bisection finds the minimum 1-October fill
that keeps the simulation feasible across all 182 days.
"""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd

from .constants import (
    CAPACITY_TWH, MONTH_ORDER, DAYS_IN_MONTH,
)


def build_day_series(
    peak_demand: pd.Series,
    scenario_imports: pd.Series,
    *,
    month_order: list[int] = MONTH_ORDER,
    days_in_month: dict[int, int] = DAYS_IN_MONTH,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Expand monthly data into per-day arrays over Oct 1 → Mar 31.

    Returns (months, peaks, imports, gaps) — each a 1-D numpy array of
    length sum(days_in_month[m] for m in month_order).
    """
    months, peaks, imps, gaps = [], [], [], []
    for m in month_order:
        d = days_in_month[m]
        p = float(peak_demand.loc[m])
        i = float(scenario_imports.loc[m])
        g = max(0.0, p - i)
        months.extend([m] * d)
        peaks.extend([p] * d)
        imps.extend([i] * d)
        gaps.extend([g] * d)
    return (np.array(months), np.array(peaks), np.array(imps), np.array(gaps))


def simulate(
    start_fill_pct: float,
    scenario_key: str,
    monthly_imports: dict[str, pd.Series],
    wc_func: Callable[[float], float],
    peak_demand: pd.Series,
    *,
    capacity_TWh: float = CAPACITY_TWH,
    month_order: list[int] = MONTH_ORDER,
    days_in_month: dict[int, int] = DAYS_IN_MONTH,
    end_of_march_floor_TWh: float = 0.5,
) -> dict:
    """Simulate the full Oct–Mar season from a given starting fill.

    Parameters
    ----------
    start_fill_pct:
        Starting fill level (0–100 %).
    scenario_key:
        Key into ``monthly_imports`` dict (e.g. "S2").
    monthly_imports:
        Dict mapping scenario key → pd.Series of monthly import GWh/d.
    wc_func:
        Withdrawal-capacity callable: fill_pct → max deliverable GWh/d.
    peak_demand:
        pd.Series indexed by month_num; 1-in-20 peak-day demand (GWh/d).
    end_of_march_floor_TWh:
        Minimum required fill at end of March 31 (TWh).  The simulation is
        infeasible if the season ends below this floor, which represents the
        ~0.5 TWh operational reserve recommended as a standalone regulatory
        instrument (covers ~5 days of the S2 March peak gap before injection
        season begins).  Set to 0.0 to disable.

    Returns
    -------
    dict with keys: feasible, min_fill_pct, day_of_infeasibility,
    binding_constraint, fill_trajectory, withdrawal_trajectory,
    headroom_trajectory, daily_gap.
    """
    _, _, _, gaps = build_day_series(
        peak_demand, monthly_imports[scenario_key],
        month_order=month_order, days_in_month=days_in_month,
    )
    n = len(gaps)
    fill_traj = np.empty(n + 1)
    fill_traj[0] = float(start_fill_pct)
    wd_traj  = np.empty(n)
    headroom = np.empty(n)
    feasible = True
    day_inf  = None
    binding  = None
    delta    = 1.0 / (capacity_TWh * 10)  # % points per GWh withdrawn

    for t in range(n):
        max_wc = wc_func(fill_traj[t])
        wd_traj[t]  = max_wc
        headroom[t] = max_wc - gaps[t]
        if max_wc < gaps[t] - 1e-9:
            feasible = False; day_inf = t; binding = "withdrawal rate"; break
        fill_traj[t + 1] = fill_traj[t] - gaps[t] * delta
        if fill_traj[t + 1] < -1e-9:
            feasible = False; day_inf = t; binding = "volume"; break

    # End-of-March operational floor (applied after season completes)
    if feasible and end_of_march_floor_TWh > 0:
        end_fill_TWh = fill_traj[n] * capacity_TWh / 100
        if end_fill_TWh < end_of_march_floor_TWh - 1e-9:
            feasible = False
            binding  = "end-of-season floor"

    valid = day_inf if day_inf is not None else n
    return {
        "feasible":             feasible,
        "min_fill_pct":         float(fill_traj[: valid + 1].min()),
        "day_of_infeasibility": day_inf,
        "binding_constraint":   binding,
        "fill_trajectory":      fill_traj[: valid + 1].tolist(),
        "withdrawal_trajectory": wd_traj[:valid].tolist(),
        "headroom_trajectory":  headroom[:valid].tolist(),
        "daily_gap":            gaps,
    }


def min_start_fill(
    scenario_key: str,
    monthly_imports: dict[str, pd.Series],
    wc_func: Callable[[float], float],
    peak_demand: pd.Series,
    *,
    capacity_TWh: float = CAPACITY_TWH,
    tol: float = 0.01,
    lo: float = 0.0,
    hi: float = 100.0,
    month_order: list[int] = MONTH_ORDER,
    days_in_month: dict[int, int] = DAYS_IN_MONTH,
    end_of_march_floor_TWh: float = 0.5,
) -> float | None:
    """Bisect for the minimum feasible 1-October starting fill (%).

    Returns ``None`` if infeasible even at ``hi`` (100 % fill).
    Returns ``lo`` (0.0) if already feasible with empty storage.
    """
    sim_kwargs = dict(
        monthly_imports=monthly_imports,
        wc_func=wc_func,
        peak_demand=peak_demand,
        capacity_TWh=capacity_TWh,
        month_order=month_order,
        days_in_month=days_in_month,
        end_of_march_floor_TWh=end_of_march_floor_TWh,
    )

    def _sim(fp: float) -> bool:
        return simulate(fp, scenario_key, **sim_kwargs)["feasible"]

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


def run_all_scenarios(
    monthly_imports: dict[str, pd.Series],
    wc_func: Callable[[float], float],
    peak_demand: pd.Series,
    scenarios: dict,
    *,
    capacity_TWh: float = CAPACITY_TWH,
    month_order: list[int] = MONTH_ORDER,
    days_in_month: dict[int, int] = DAYS_IN_MONTH,
    end_of_march_floor_TWh: float = 0.5,
) -> dict:
    """Run season-target bisection for all scenarios.

    Returns dict: results[scenario_key] = {start_fill_pct, start_fill_TWh,
    binding, sim}.
    """
    results: dict = {}
    for key in scenarios:
        f = min_start_fill(
            key, monthly_imports, wc_func, peak_demand,
            capacity_TWh=capacity_TWh,
            month_order=month_order,
            days_in_month=days_in_month,
            end_of_march_floor_TWh=end_of_march_floor_TWh,
        )
        sim = simulate(
            f if f is not None else 0.0,
            key, monthly_imports, wc_func, peak_demand,
            capacity_TWh=capacity_TWh,
            month_order=month_order,
            days_in_month=days_in_month,
            end_of_march_floor_TWh=end_of_march_floor_TWh,
        ) if f is not None else None

        # Determine binding constraint by probing just below minimum fill
        if f is None:
            binding = "infeasible at 100%"
        else:
            probe = simulate(
                max(0.0, f - 0.05), key, monthly_imports, wc_func, peak_demand,
                capacity_TWh=capacity_TWh,
                month_order=month_order,
                days_in_month=days_in_month,
                end_of_march_floor_TWh=end_of_march_floor_TWh,
            )
            binding = probe["binding_constraint"] or "volume"

        results[key] = {
            "start_fill_pct": f,
            "start_fill_TWh": None if f is None else round(f * capacity_TWh / 100, 2),
            "binding": binding,
            "sim": sim,
        }
    return results


def sensitivity_table(
    scenarios: dict,
    monthly_imports: dict[str, pd.Series],
    base_wc_func: Callable[[float], float],
    peak_demand: pd.Series,
    *,
    wc_abs_func: Callable[[float], float] | None = None,
    capacity_TWh: float = CAPACITY_TWH,
    peak_shifts: tuple[float, ...] = (0.0, +50.0, -50.0),
) -> pd.DataFrame:
    """Build the peak-demand sensitivity table for all scenarios.

    Columns: base_TWh, peak+N_TWh, peak-N_TWh, and optionally wc_abs_TWh.
    """
    rows = []
    for key in scenarios:
        row = {"scenario": key}
        for shift in peak_shifts:
            shifted = peak_demand + shift
            f = min_start_fill(
                key, monthly_imports, base_wc_func, shifted,
                capacity_TWh=capacity_TWh,
            )
            col = "base_TWh" if shift == 0 else f"peak {shift:+.0f}_TWh"
            row[col] = round(f * capacity_TWh / 100, 2) if f is not None else None
        if wc_abs_func is not None:
            f_abs = min_start_fill(
                key, monthly_imports, wc_abs_func, peak_demand,
                capacity_TWh=capacity_TWh,
            )
            row["wc_abs curve_TWh"] = round(f_abs * capacity_TWh / 100, 2) if f_abs is not None else None
        rows.append(row)
    return pd.DataFrame(rows).set_index("scenario")
