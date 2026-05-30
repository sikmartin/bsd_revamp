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
    ("S1", 25.2),
    ("S2", 21.9),
    ("S3", 17.0),
    ("S4",  9.9),
    ("S5",  5.3),
])
def test_season_targets(setup, key, expected_twh):
    results, *_ = setup
    got = results[key]["start_fill_TWh"]
    assert abs(got - expected_twh) <= TOL, f"{key}: got {got}, expected {expected_twh}"


def test_s1_binding_withdrawal_rate(setup):
    results, *_ = setup
    assert results["S1"]["binding"] == "withdrawal rate"


@pytest.mark.parametrize("key", ["S2", "S3", "S4", "S5"])
def test_s2_s5_binding_volume(setup, key):
    results, *_ = setup
    assert results[key]["binding"] == "volume"


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
    r = bsd.simulate(50.0, "S2", imp, wc_func, prof.peak)
    # 182 days total (31+30+31+31+28+31)
    assert len(r["headroom_trajectory"]) == 182


def test_build_day_series_length(setup):
    _, imp, wc_func, prof = setup
    _, _, _, gaps = bsd.build_day_series(prof.peak, imp["S2"])
    assert len(gaps) == 182


def test_min_start_fill_s2(setup):
    _, imp, wc_func, prof = setup
    f = bsd.min_start_fill("S2", imp, wc_func, prof.peak)
    assert abs(f * bsd.CAPACITY_TWH / 100 - 21.9) <= TOL


def test_sensitivity_table_shape(setup):
    results, imp, wc_func, prof = setup
    df = bsd.sensitivity_table(
        bsd.DEFAULT_SCENARIOS_DICT, imp, wc_func, prof.peak,
        peak_shifts=(0.0, +50.0, -50.0),
    )
    assert df.shape == (5, 3)
    assert abs(df.loc["S2", "base_TWh"] - 21.9) <= TOL
    assert abs(df.loc["S2", "peak +50_TWh"] - 30.48) <= 0.5
