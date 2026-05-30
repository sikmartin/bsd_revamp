"""Withdrawal-capacity curves: empirical P95 isotonic fit, ENTSOG engineering, and blends."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from sklearn.isotonic import IsotonicRegression

from .constants import (
    WC_BIN_EDGES, WC_BIN_QUANTILE, WC_MIN_OBS, WC_DEFAULT_HAIRCUT, MONTH_ORDER
)
from .data import DATA_PATH_STORAGE_GIE, DEFAULT_CUTOFF, WINTER_MONTHS


@dataclass
class WcCurves:
    """Container for the three withdrawal-capacity curves fitted from a single dataset.

    ``empirical``     — relative isotonic P95 (ratio-scaled to WC_CURRENT): conservative floor.
    ``empirical_abs`` — absolute isotonic P95: not ratio-scaled; used for sensitivity only.
    ``engineering``   — ENTSOG declared capacity with haircut: physical ceiling.
    ``wc_current``    — latest declared withdrawal capacity (GWh/d); used for ratio-scaling.
    """
    empirical: Callable[[float], float]
    empirical_abs: Callable[[float], float]
    engineering: Callable[[float], float]
    wc_current: float

    def blend(self, eng_weight: float) -> Callable[[float], float]:
        """Return a weighted-average blend callable.

        ``eng_weight`` is the weight on the engineering curve (0 = pure empirical,
        1 = pure engineering).  Branch 1 default: 0.50.  Branch 2 default: 0.75.
        """
        emp = self.empirical
        eng = self.engineering
        return lambda fp: (1.0 - eng_weight) * emp(fp) + eng_weight * eng(fp)


def fit_withdrawal_curves(
    *,
    gio_path: str | Path = DATA_PATH_STORAGE_GIE,
    cutoff: str | None = DEFAULT_CUTOFF,
    eng_path: str | Path = "data/cz_usg_withdrawal_curve_2025.csv",
    haircut: float = WC_DEFAULT_HAIRCUT,
    bin_quantile: float = WC_BIN_QUANTILE,
    min_obs: int = WC_MIN_OBS,
    month_order: list[int] = MONTH_ORDER,
) -> WcCurves:
    """Fit all withdrawal-capacity curves from GIE storage data.

    Parameters
    ----------
    gio_path:
        Path to the GIE storage CSV (semicolon-separated).
    cutoff:
        Include only observations on or after this date (post-2022 default).
    eng_path:
        Path to the ENTSOG engineering withdrawal-curve CSV.
    haircut:
        Multiplicative reduction applied to the engineering curve (default 10%).
    bin_quantile:
        Quantile used for the empirical fit within each fill bin (default P95).
    min_obs:
        Minimum observations per 5%-bin for it to be included in the isotonic fit.
    """
    raw = pd.read_csv(
        gio_path, sep=";",
        parse_dates=["Gas Day Start (status at 6AM  CEST)"],
        dayfirst=False, decimal=".",
    )
    raw.columns = raw.columns.str.strip()
    raw = raw.rename(columns={
        "Gas Day Start (status at 6AM  CEST)": "date",
        "Full (%)":                            "fill_pct",
        "Withdrawal (GWh/d)":                  "withdrawal",
        "Withdrawal capacity (GWh/d)":         "wc_declared",
    })
    sto = raw[["date", "fill_pct", "withdrawal", "wc_declared"]].dropna()
    sto["month"] = sto["date"].dt.month
    wint = sto[
        (sto["date"] >= cutoff) & sto["month"].isin(WINTER_MONTHS)
    ].copy()
    wint["util_ratio"] = wint["withdrawal"] / wint["wc_declared"]

    # WC_CURRENT: declared capacity on the latest data day
    wc_current = float(wint.loc[wint["date"] == wint["date"].max(), "wc_declared"].iloc[0])

    bin_edges = np.array(WC_BIN_EDGES, dtype=float)
    bin_labels = (bin_edges[:-1] + 2.5)
    wint["fill_bin"] = pd.cut(
        wint["fill_pct"], bins=bin_edges, labels=bin_labels, right=False
    ).astype(float)

    bins = (
        wint.groupby("fill_bin", observed=False)
        .agg(
            n=("withdrawal", "count"),
            p_abs=("withdrawal",   lambda x: x.quantile(bin_quantile)),
            p_ratio=("util_ratio", lambda x: x.quantile(bin_quantile)),
        )
        .reset_index()
        .rename(columns={"fill_bin": "fill_mid"})
    )
    bins["p_rel"] = bins["p_ratio"] * wc_current
    bins["reliable"] = bins["n"] >= min_obs

    reliable = bins[bins["reliable"]]
    fill_all = bins["fill_mid"].values

    ir_rel = IsotonicRegression(increasing=True, out_of_bounds="clip")
    ir_rel.fit(reliable["fill_mid"], reliable["p_rel"])
    bins["curve_rel"] = ir_rel.predict(fill_all)

    ir_abs = IsotonicRegression(increasing=True, out_of_bounds="clip")
    ir_abs.fit(reliable["fill_mid"], reliable["p_abs"])
    bins["curve_abs"] = ir_abs.predict(fill_all)

    _interp_rel = interp1d(
        fill_all, bins["curve_rel"].values, kind="linear",
        bounds_error=False,
        fill_value=(bins["curve_rel"].iloc[0], bins["curve_rel"].iloc[-1]),
    )
    _interp_abs = interp1d(
        fill_all, bins["curve_abs"].values, kind="linear",
        bounds_error=False,
        fill_value=(bins["curve_abs"].iloc[0], bins["curve_abs"].iloc[-1]),
    )

    def wc_empirical(fp: float) -> float:
        return float(_interp_rel(np.clip(fp, 0, 100)))

    def wc_empirical_abs(fp: float) -> float:
        return float(_interp_abs(np.clip(fp, 0, 100)))

    # ENTSOG engineering curve with haircut
    eng = pd.read_csv(Path(eng_path)).sort_values("percentile")
    eng_fill  = eng["percentile"].values * 100
    eng_ratio = eng["value"].values * (1.0 - haircut)
    _interp_eng = interp1d(
        eng_fill, eng_ratio * wc_current, kind="linear",
        bounds_error=False,
        fill_value=(eng_ratio[0] * wc_current, eng_ratio[-1] * wc_current),
    )

    def wc_engineering(fp: float) -> float:
        return float(_interp_eng(np.clip(fp, 0, 100)))

    return WcCurves(
        empirical=wc_empirical,
        empirical_abs=wc_empirical_abs,
        engineering=wc_engineering,
        wc_current=wc_current,
    )
