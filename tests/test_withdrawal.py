"""Tests for bsd.withdrawal — curve fitting and blend factory."""

import pytest
import bsd


@pytest.fixture(scope="module")
def curves():
    return bsd.fit_withdrawal_curves()


def test_wc_current_positive(curves):
    assert curves.wc_current > 0


def test_empirical_monotone(curves):
    vals = [curves.empirical(fp) for fp in range(0, 101, 10)]
    assert all(b >= a - 1e-6 for a, b in zip(vals, vals[1:]))


def test_engineering_monotone(curves):
    vals = [curves.engineering(fp) for fp in range(0, 101, 10)]
    assert all(b >= a - 1e-6 for a, b in zip(vals, vals[1:]))


def test_blend_between_empirical_and_engineering(curves):
    b5050 = curves.blend(0.50)
    for fp in [20, 40, 60, 80]:
        emp = curves.empirical(fp)
        eng = curves.engineering(fp)
        blend_val = b5050(fp)
        lo, hi = min(emp, eng), max(emp, eng)
        assert lo - 1e-6 <= blend_val <= hi + 1e-6


def test_blend_50_50_at_key_levels(curves):
    b = curves.blend(0.50)
    assert abs(b(20) - 244.6) < 1.0
    assert abs(b(40) - 445.5) < 1.0


def test_blend_75_25_at_key_levels(curves):
    b = curves.blend(0.75)
    assert abs(b(20) - 303.5) < 1.0
    assert abs(b(50) - 568.5) < 1.0
