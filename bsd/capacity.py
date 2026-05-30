"""
capacity.py — Reliable import capacity percentiles and storage gap scenarios.

The central question this module answers is:

    "Given a 1-in-20 peak demand estimate (GWh/d), how much gas must be
     available from Czech underground storage to cover the shortfall between
     that demand and what can reliably be imported — sustained over 30 days?"

The answer depends on how conservatively we define 'reliable import'.  Rather
than picking a single number, we present a set of named scenarios that pair a
confidence level on imports with a plain-language description, so the result
can be used directly in a risk discussion.

Key concepts
------------
Single-day percentile (P_k):
    The k-th percentile of the empirical daily import distribution over
    winter days.  Reading: "On k% of winter days, imports were at or below
    this level."  We use *lower* percentiles as the conservative (stressed)
    end of the range, e.g. P10 = imports exceeded this on 90% of days.

30-day rolling average percentile:
    The k-th percentile of the distribution of 30-day rolling averages,
    evaluated over winter days.  This is more relevant than the single-day
    figure for storage sizing because storage must sustain a withdrawal rate
    over weeks, not just cover a single peak day.

Storage gap (30-day):
    max(0, peak_demand − 30d_sustained_import) × 30
    Units: GWh.  This is the minimum working-gas volume that must be
    available in Czech UGS at the start of the cold period to bridge the
    shortfall for 30 consecutive days.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import pandas as pd

from .data import WINTER_MONTHS


# ---------------------------------------------------------------------------
# Scenario definitions
# ---------------------------------------------------------------------------

@dataclass
class Scenario:
    """A named import-reliability scenario used for storage sizing.

    Attributes
    ----------
    label:
        Short human-readable name shown in tables and charts.
    import_percentile:
        The lower-tail percentile of the winter import distribution used as
        the 'reliable import' level for this scenario.  For example, 10
        means "imports were above this level on 90% of observed winter days",
        which is a conservative (high-confidence) assumption.
    description:
        One-sentence narrative describing the market/weather context.
    """
    label: str
    import_percentile: int
    description: str


#: Default scenario set covering the range from high-stress to favourable.
#: Callers may pass a custom list to ``storage_scenarios()``.
DEFAULT_SCENARIOS: list[Scenario] = [
    Scenario(
        label="S1 — High stress",
        import_percentile=10,
        description=(
            "Severe import shortfall (1-in-10 winter days worse than this). "
            "Represents a prolonged cold spell coinciding with low German "
            "hub supply or a single-corridor disruption."
        ),
    ),
    Scenario(
        label="S2 — Stressed",
        import_percentile=20,
        description=(
            "Significant import shortfall (1-in-5 winter days worse). "
            "Credible planning anchor: pairs a 1-in-20 demand event with a "
            "1-in-5 import shortfall for a joint severity of roughly 1-in-100."
        ),
    ),
    Scenario(
        label="S3 — Base stressed",
        import_percentile=30,
        description=(
            "Moderate import shortfall (1-in-3 winter days worse). "
            "Represents a cold week with tighter-than-normal German supply "
            "but no single corridor failure."
        ),
    ),
    Scenario(
        label="S4 — Median",
        import_percentile=50,
        description=(
            "Median import conditions. Half of observed winter days had "
            "lower imports than this.  A reasonable central-case baseline."
        ),
    ),
    Scenario(
        label="S5 — Favourable",
        import_percentile=70,
        description=(
            "Above-average imports (only 30% of winter days higher). "
            "Optimistic supply conditions; useful as a lower bound on "
            "storage requirements."
        ),
    ),
]


# ---------------------------------------------------------------------------
# Core calculations
# ---------------------------------------------------------------------------

def winter_daily(daily: pd.DataFrame) -> pd.DataFrame:
    """Return only the winter rows (Nov–Mar) from a daily import DataFrame."""
    return daily[daily["month"].isin(WINTER_MONTHS)].copy()


def add_rolling_avg(daily: pd.DataFrame, window: int = 30) -> pd.DataFrame:
    """Add a rolling-average column to a daily import DataFrame.

    The rolling average is computed over the *full* date-sorted series (not
    just winter days) so that a cold spell starting in late October carries
    the correct 30-day context into November.  The result is then available
    for all rows; callers can filter to winter days afterwards.

    Parameters
    ----------
    daily:
        Output of ``data.load_daily_imports()``, sorted by date.
    window:
        Number of days in the rolling window.  Default is 30 to match the
        storage-sizing horizon.

    Returns
    -------
    pd.DataFrame
        Same as input with an extra column ``roll{window}_avg_GWh_d``.
    """
    col = f"roll{window}_avg_GWh_d"
    out = daily.copy()
    out[col] = out["GWh_d"].rolling(window, min_periods=window).mean()
    return out


def import_percentile_table(
    daily: pd.DataFrame,
    percentiles: Sequence[int] = (5, 10, 20, 30, 50, 70, 80, 90, 95),
    winter_only: bool = True,
    rolling_window: int = 30,
) -> pd.DataFrame:
    """Return a table of import-level percentiles for single-day and 30-day
    rolling averages.

    Parameters
    ----------
    daily:
        Output of ``data.load_daily_imports()``.
    percentiles:
        Sequence of integer percentile values to compute (0–100).
    winter_only:
        If ``True`` (default), restrict to Nov–Mar days only.
    rolling_window:
        Rolling average window in days.

    Returns
    -------
    pd.DataFrame
        Index: percentile values.  Columns: ``single_day_GWh_d``,
        ``roll{N}_avg_GWh_d``.
    """
    enriched = add_rolling_avg(daily, window=rolling_window)
    subset = winter_daily(enriched) if winter_only else enriched

    roll_col = f"roll{rolling_window}_avg_GWh_d"
    roll_series = subset[roll_col].dropna()

    rows = []
    for p in percentiles:
        rows.append({
            "percentile": p,
            "single_day_GWh_d": subset["GWh_d"].quantile(p / 100),
            roll_col: roll_series.quantile(p / 100),
        })

    return pd.DataFrame(rows).set_index("percentile")


def storage_scenarios(
    daily: pd.DataFrame,
    peak_demand_GWh_d: float,
    scenarios: list[Scenario] = DEFAULT_SCENARIOS,
    rolling_window: int = 30,
) -> pd.DataFrame:
    """Compute the 30-day storage requirement for each scenario.

    For each scenario the function looks up the empirical lower-tail
    percentile of (a) single-day winter imports and (b) 30-day rolling
    average winter imports, then computes:

        daily_gap        = max(0, peak_demand − 30d_sustained_import)
        storage_30d_GWh  = daily_gap × 30
        storage_30d_TWh  = storage_30d_GWh / 1000

    Parameters
    ----------
    daily:
        Output of ``data.load_daily_imports()``.
    peak_demand_GWh_d:
        The 1-in-20 peak daily demand estimate in GWh/d.  This is treated
        as exogenous (provided by the demand analyst).
    scenarios:
        List of ``Scenario`` objects.  Defaults to ``DEFAULT_SCENARIOS``.
    rolling_window:
        Rolling average window in days (default 30 to match storage horizon).

    Returns
    -------
    pd.DataFrame
        One row per scenario with columns:
        ``label``, ``import_percentile``, ``description``,
        ``reliable_import_daily_GWh_d``, ``reliable_import_30d_avg_GWh_d``,
        ``daily_gap_GWh_d``, ``storage_30d_GWh``, ``storage_30d_TWh``.
    """
    ptable = import_percentile_table(
        daily,
        percentiles=[s.import_percentile for s in scenarios],
        winter_only=True,
        rolling_window=rolling_window,
    )
    roll_col = f"roll{rolling_window}_avg_GWh_d"

    rows = []
    for s in scenarios:
        p = s.import_percentile
        daily_import = ptable.loc[p, "single_day_GWh_d"]
        sustained_import = ptable.loc[p, roll_col]
        daily_gap = max(0.0, peak_demand_GWh_d - sustained_import)
        storage_gwh = daily_gap * rolling_window

        rows.append({
            "label": s.label,
            "import_percentile": p,
            "description": s.description,
            "reliable_import_daily_GWh_d": round(daily_import, 1),
            f"reliable_import_{rolling_window}d_avg_GWh_d": round(sustained_import, 1),
            "daily_gap_GWh_d": round(daily_gap, 1),
            "storage_30d_GWh": round(storage_gwh, 0),
            "storage_30d_TWh": round(storage_gwh / 1000, 2),
        })

    return pd.DataFrame(rows)


def seasonal_peaks(daily: pd.DataFrame) -> pd.DataFrame:
    """Summarise peak and average imports for each gas-winter season.

    Useful as a quick sense-check: the table shows how much the post-2022
    seasons differ from the 2019–2022 Russian-transit era.

    Returns
    -------
    pd.DataFrame
        Index: gas-winter label (e.g. '2022/23').
        Columns: ``peak_GWh_d``, ``p90_GWh_d``, ``median_GWh_d``,
                 ``mean_GWh_d``, ``n_days``.
    """
    from .data import gas_winter_label

    w = winter_daily(daily).copy()
    w["gas_winter"] = gas_winter_label(w["date"])
    w = w.dropna(subset=["gas_winter"])

    summary = (
        w.groupby("gas_winter")["GWh_d"]
        .agg(
            peak_GWh_d="max",
            p90_GWh_d=lambda x: x.quantile(0.9),
            median_GWh_d="median",
            mean_GWh_d="mean",
            n_days="count",
        )
        .round(1)
    )

    return summary
