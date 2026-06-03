"""Tests for bsd.target — Branch 2 season-long fill target."""

import pytest
import pandas as pd
import bsd

TOL = 0.05  # TWh tolerance


@pytest.fixture(scope="module")
def setup():
    prof = bsd.load_demand_profile()
    curves = bsd.fit_withdrawal_curves()
    wc_func = curves.blend(eng_weight=0.75)
    imp = bsd.compute_monthly_imports(bsd.DEFAULT_SCENARIOS_DICT)
    results = bsd.run_all_scenarios(imp, wc_func, prof.peak, bsd.DEFAULT_SCENARIOS_DICT)
    return results, imp, wc_func, prof


# ── Published S1–S5 headlines ───────────────────────────────────────────────

@pytest.mark.parametrize("key,expected_twh", [
    ("S1", 25.96),
    ("S2", 22.71),
    ("S3", 17.85),
    ("S4", 10.50),
    ("S5",  5.79),
])
def test_season_targets(setup, key, expected_twh):
    results, *_ = setup
    got = results[key]["start_fill_TWh"]
    assert abs(got - expected_twh) <= TOL, f"{key}: got {got}, expected {expected_twh}"


@pytest.mark.parametrize("key", ["S1", "S2", "S3", "S4", "S5"])
def test_all_binding_end_of_season_floor(setup, key):
    results, *_ = setup
    assert results[key]["binding"] == "end-of-season floor"


# ── Simulate unit tests ──────────────────────────────────────────────────────

def test_simulate_feasible_at_100pct(setup):
    _, imp, wc_func, prof = setup
    r = bsd.simulate(100.0, "S2", imp, wc_func, prof.peak)
    assert r["feasible"] is True


def test_simulate_infeasible_at_zero_s1(setup):
    _, imp, wc_func, prof = setup
    r = bsd.simulate(0.0, "S1", imp, wc_func, prof.peak)
    assert r["feasible"] is False


def test_simulate_returns_headroom_trajectory(setup):
    _, imp, wc_func, prof = setup
    r = bsd.simulate(70.0, "S2", imp, wc_func, prof.peak)  # 70% > S2 min (~55%)
    # 182 days total (31+30+31+31+28+31)
    assert len(r["headroom_trajectory"]) == 182


def test_build_day_series_length(setup):
    _, imp, wc_func, prof = setup
    _, _, _, gaps = bsd.build_day_series(prof.peak, imp["S2"])
    assert len(gaps) == 182


def test_min_start_fill_s2(setup):
    _, imp, wc_func, prof = setup
    f = bsd.min_start_fill("S2", imp, wc_func, prof.peak)
    assert abs(f * bsd.CAPACITY_TWH / 100 - 22.71) <= TOL


def test_sensitivity_table_shape(setup):
    results, imp, wc_func, prof = setup
    df = bsd.sensitivity_table(
        bsd.DEFAULT_SCENARIOS_DICT, imp, wc_func, prof.peak,
        peak_shifts=(0.0, +50.0, -50.0),
    )
    assert df.shape == (5, 3)
    assert abs(df.loc["S2", "base_TWh"] - 22.71) <= TOL
    assert abs(df.loc["S2", "peak +50_TWh"] - 30.06) <= 0.5
