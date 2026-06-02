"""
plot.py — Reusable chart functions for the import-capacity analysis.

All functions return a ``matplotlib.figure.Figure`` so they can be displayed
inline in a Jupyter notebook (``fig`` is the last expression in a cell) or
saved to disk (``fig.savefig(...)``).  None of them call ``plt.show()``
directly, which keeps them composable and testable.

Chart inventory
---------------
daily_imports_timeseries  — full time series with structural-break annotation
winter_daily_histogram    — distribution of winter daily imports with
                            percentile markers
winter_cdf                — empirical CDF with scenario thresholds overlaid
scenario_bar              — horizontal bar chart of 30-day storage requirements
source_stacked_area       — corridor-level stacked area chart
"""


import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

from . import jvs

jvs.apply_style(theme="light", context="notebook")

# ---------------------------------------------------------------------------
# Style helpers
# ---------------------------------------------------------------------------

#: Colour palette — one colour per scenario, ordered S1→S5.
SCENARIO_COLOURS = ["#c0392b", "#e67e22", "#f1c40f", "#27ae60", "#2980b9"]

#: Colour for the structural-break annotation line.
BREAK_COLOUR = "#7f8c8d"


def _apply_base_style(ax: plt.Axes) -> None:
    """Apply a clean, minimal style to an axes object."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=9)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))


# ---------------------------------------------------------------------------
# 1. Full time series
# ---------------------------------------------------------------------------

def daily_imports_timeseries(
    daily_full: pd.DataFrame,
    cutoff: pd.Timestamp | None = None,
    title: str = "Czech balancing zone — daily imports (excl. storage)",
) -> plt.Figure:
    """Plot the full daily import time series with optional structural-break line.

    Parameters
    ----------
    daily_full:
        Output of ``data.load_daily_imports()`` with *no* cutoff applied
        (pass ``cutoff=pd.Timestamp('2020-01-01')`` or similar when calling
        ``load_daily_imports`` to get the full history).
    cutoff:
        If provided, draw a vertical dashed line at this date and annotate
        it as the analytical cutoff.
    title:
        Chart title.

    Returns
    -------
    matplotlib.figure.Figure
    """
    if cutoff is not None:
        cutoff = pd.Timestamp(cutoff)

    fig, ax = plt.subplots(figsize=(12, 4))

    ax.plot(
        daily_full["date"],
        daily_full["GWh_d"],
        linewidth=0.7,
        color="#2c3e50",
        alpha=0.85,
        label="Daily import (GWh/d)",
    )

    if cutoff is not None:
        ax.axvline(cutoff, color=BREAK_COLOUR, linestyle="--", linewidth=1.2)
        ax.text(
            cutoff,
            ax.get_ylim()[1] * 0.95,
            "  Analytical cutoff\n  (Mar 2022)",
            color=BREAK_COLOUR,
            fontsize=8,
            va="top",
        )
        # Shade the excluded pre-cutoff region.
        ax.axvspan(daily_full["date"].min(), cutoff, alpha=0.06, color=BREAK_COLOUR)

    ax.set_title(title, fontsize=11, pad=8)
    ax.set_ylabel("GWh / day")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")
    _apply_base_style(ax)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# 2. Winter daily import histogram
# ---------------------------------------------------------------------------

def winter_daily_histogram(
    daily: pd.DataFrame,
    percentiles: list[int] | None = None,
    title: str = "Distribution of winter daily imports (post-Mar 2022, Nov–Mar)",
) -> plt.Figure:
    """Histogram of winter daily imports with percentile marker lines.

    Parameters
    ----------
    daily:
        Output of ``data.load_daily_imports()``.
    percentiles:
        List of integer percentile values to annotate.  Defaults to
        [10, 20, 30, 50, 70].
    title:
        Chart title.
    """
    from .data import WINTER_MONTHS

    if percentiles is None:
        percentiles = [10, 20, 30, 50, 70]

    winter_vals = daily.loc[daily["month"].isin(WINTER_MONTHS), "GWh_d"]

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.hist(winter_vals, bins=40, color="#2980b9", alpha=0.7, edgecolor="white", linewidth=0.4)

    for i, p in enumerate(percentiles):
        val = winter_vals.quantile(p / 100)
        colour = SCENARIO_COLOURS[i % len(SCENARIO_COLOURS)]
        ax.axvline(val, color=colour, linewidth=1.4, linestyle="--")
        ax.text(
            val + 3,
            ax.get_ylim()[1] * (0.92 - i * 0.08),
            f"P{p}: {val:.0f}",
            color=colour,
            fontsize=8,
        )

    ax.set_xlabel("GWh / day")
    ax.set_ylabel("Number of days")
    ax.set_title(title, fontsize=11, pad=8)
    _apply_base_style(ax)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# 3. Empirical CDF
# ---------------------------------------------------------------------------

def winter_cdf(
    daily: pd.DataFrame,
    scenarios: list | None = None,
    peak_demand_GWh_d: float | None = None,
    title: str = "Empirical CDF — winter daily imports (post-Mar 2022, Nov–Mar)",
) -> plt.Figure:
    """Empirical CDF with optional scenario threshold and peak-demand lines.

    Parameters
    ----------
    daily:
        Output of ``data.load_daily_imports()``.
    scenarios:
        List of ``capacity.Scenario`` objects.  If provided, each scenario's
        import percentile is marked on the CDF curve.
    peak_demand_GWh_d:
        If provided, draw a vertical line showing the 1-in-20 demand level
        for reference.
    title:
        Chart title.
    """
    from .data import WINTER_MONTHS

    winter_vals = daily.loc[daily["month"].isin(WINTER_MONTHS), "GWh_d"].sort_values()
    cdf = pd.Series(range(1, len(winter_vals) + 1), index=winter_vals.values) / len(winter_vals)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(cdf.index, cdf.values * 100, color="#2c3e50", linewidth=1.5, label="Empirical CDF")

    if scenarios is not None:
        for i, s in enumerate(scenarios):
            val = winter_vals.quantile(s.import_percentile / 100)
            colour = SCENARIO_COLOURS[i % len(SCENARIO_COLOURS)]
            ax.plot(val, s.import_percentile, "o", color=colour, markersize=6, zorder=5)
            ax.annotate(
                f" {s.label.split('—')[0].strip()}\n {val:.0f} GWh/d",
                xy=(val, s.import_percentile),
                fontsize=7.5,
                color=colour,
            )

    if peak_demand_GWh_d is not None:
        ax.axvline(peak_demand_GWh_d, color="#e74c3c", linewidth=1.3, linestyle=":")
        ax.text(
            peak_demand_GWh_d + 5,
            5,
            f"1-in-20 demand\n{peak_demand_GWh_d:.0f} GWh/d",
            color="#e74c3c",
            fontsize=8,
        )

    ax.set_xlabel("Daily import level (GWh/d)")
    ax.set_ylabel("Cumulative probability (%)")
    ax.set_title(title, fontsize=11, pad=8)
    ax.set_ylim(0, 100)
    _apply_base_style(ax)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# 4. Scenario storage requirement bar chart
# ---------------------------------------------------------------------------

def scenario_bar(
    results: pd.DataFrame,
    czechugs_capacity_TWh: float = 3.4,
    title: str = "30-day storage requirement by import scenario",
) -> plt.Figure:
    """Horizontal bar chart of 30-day storage requirements across scenarios.

    Parameters
    ----------
    results:
        Output of ``capacity.storage_scenarios()``.
    czechugs_capacity_TWh:
        Total Czech UGS working-gas capacity in TWh.  A reference line is
        drawn at this level so readers can see immediately which scenarios
        exceed domestic storage capacity.
    title:
        Chart title.
    """
    fig, ax = plt.subplots(figsize=(9, 4))

    labels = results["label"].str.split("—").str[0].str.strip()
    values = results["storage_30d_TWh"]
    colours = SCENARIO_COLOURS[: len(results)]

    bars = ax.barh(labels, values, color=colours, alpha=0.85, height=0.55)

    # Value labels on bars.
    for bar, val in zip(bars, values):
        ax.text(
            val + 0.03,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.2f} TWh",
            va="center",
            fontsize=9,
        )

    # Czech UGS capacity reference line.
    ax.axvline(czechugs_capacity_TWh, color="#e74c3c", linewidth=1.4, linestyle="--")
    ax.text(
        czechugs_capacity_TWh + 0.05,
        len(results) - 0.5,
        f"Czech UGS capacity\n{czechugs_capacity_TWh} TWh",
        color="#e74c3c",
        fontsize=8,
        va="top",
    )

    ax.set_xlabel("30-day storage needed (TWh)")
    ax.set_title(title, fontsize=11, pad=8)
    ax.invert_yaxis()
    _apply_base_style(ax)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# 5. Corridor stacked area chart
# ---------------------------------------------------------------------------

def source_stacked_area(
    by_source: pd.DataFrame,
    title: str = "Daily imports by corridor (post-Mar 2022)",
) -> plt.Figure:
    """Stacked area chart of daily imports split by adjacent system.

    Parameters
    ----------
    by_source:
        Output of ``data.load_daily_imports_by_source()``.
    title:
        Chart title.
    """
    # Pivot to wide format: date × source.
    wide = (
        by_source
        .groupby(["date", "adjacentSystemsLabel"])["GWh_d"]
        .sum()
        .unstack(fill_value=0)
    )

    # Drop sources that are zero throughout (reduces visual clutter).
    wide = wide.loc[:, wide.max() > 0.5]

    fig, ax = plt.subplots(figsize=(12, 4))

    palette = plt.cm.tab10.colors
    ax.stackplot(
        wide.index,
        [wide[col] for col in wide.columns],
        labels=wide.columns.tolist(),
        colors=palette[: len(wide.columns)],
        alpha=0.82,
    )

    ax.set_title(title, fontsize=11, pad=8)
    ax.set_ylabel("GWh / day")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")
    ax.legend(loc="upper right", fontsize=8, framealpha=0.6)
    _apply_base_style(ax)
    fig.tight_layout()
    return fig
