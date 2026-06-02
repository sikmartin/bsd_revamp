"""Tests for bsd.obligations — Branch 1 monthly stress simulation."""

import pytest
import bsd

TOL = 0.05  # TWh tolerance for headline comparisons


@pytest.fixture(scope="module")
def setup():
    prof = bsd.load_demand_profile()
    curves = bsd.fit_withdrawal_curves()
    wc_func = curves.blend(eng_weight=0.50)
    imp = bsd.compute_monthly_imports(bsd.DEFAULT_SCENARIOS_DICT)
    results = bsd.run_all_months(imp, wc_func, prof.peak, prof.residual,
                                  bsd.DEFAULT_SCENARIOS_DICT)
    return results, imp, wc_func, prof


# ── Published S2 headlines ──────────────────────────────────────────────────

@pytest.mark.parametrize("month,expected", [
    (10, 0.00),
    (11, 1.01),
    (12, 4.12),
    (1,  8.54),
    (2,  3.62),
    (3,  0.84),
])
def test_s2_obligations(setup, month, expected):
    results, *_ = setup
    got = results["S2"][month]["start_fill_TWh"]
    assert abs(got - expected) <= TOL, f"Month {month}: got {got}, expected {expected}"


@pytest.mark.parametrize("month,expected", [
    (12, 4.50),
    (1, 10.56),
    (2,  6.12),
])
def test_s1_jan_dec_feb(setup, month, expected):
    results, *_ = setup
    got = results["S1"][month]["start_fill_TWh"]
    assert abs(got - expected) <= TOL


def test_s5_jan(setup):
    results, *_ = setup
    assert abs(results["S5"][1]["start_fill_TWh"] - 0.67) <= TOL


def test_zero_obligations_oct_all_scenarios(setup):
    results, *_ = setup
    for key in bsd.DEFAULT_SCENARIOS_DICT:
        assert results[key][10]["start_fill_TWh"] == 0.0


# ── Simulate month unit tests ────────────────────────────────────────────────

def test_simulate_month_feasible_at_high_fill(setup):
    _, imp, wc_func, prof = setup
    r = bsd.simulate_month(
        80.0, 1, float(imp["S2"][1]), wc_func, prof.peak, prof.residual
    )
    assert r["feasible"] is True


def test_simulate_month_infeasible_at_zero_fill_jan_s1(setup):
    _, imp, wc_func, prof = setup
    r = bsd.simulate_month(
        0.0, 1, float(imp["S1"][1]), wc_func, prof.peak, prof.residual
    )
    assert r["feasible"] is False


def test_simulate_month_returns_trajectory(setup):
    _, imp, wc_func, prof = setup
    r = bsd.simulate_month(
        50.0, 1, float(imp["S2"][1]), wc_func, prof.peak, prof.residual
    )
    assert len(r["fill_trajectory"]) == 31  # 30 days + start


def test_min_start_fill_month_s2_jan(setup):
    _, imp, wc_func, prof = setup
    f = bsd.min_start_fill_month(1, float(imp["S2"][1]), wc_func, prof.peak, prof.residual)
    assert abs(f * bsd.CAPACITY_TWH / 100 - 8.54) <= TOL
