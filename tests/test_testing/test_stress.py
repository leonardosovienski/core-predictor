"""testing.stress — runner property-based stdlib: detecta violação, determinístico por seed."""
import pytest

from predictor_core.testing.stress import PropertyFailure, check_property, floats, integers, lists_of
from predictor_core.measurement.metrics import brier


def test_check_property_passes_for_true_invariant():
    def commutative(a, b):
        return a + b == b + a
    assert check_property(commutative, integers(), integers(), trials=50, seed=1) == 50


def test_check_property_catches_violation():
    def always_positive(x):
        return x > 0
    with pytest.raises(PropertyFailure):
        check_property(always_positive, integers(-10, 10), trials=50, seed=1)


def test_check_property_deterministic_by_seed():
    def flaky(x):
        return x != 7
    with pytest.raises(PropertyFailure) as e1:
        check_property(flaky, integers(0, 20), trials=200, seed=42)
    with pytest.raises(PropertyFailure) as e2:
        check_property(flaky, integers(0, 20), trials=200, seed=42)
    assert e1.value.args == e2.value.args


def test_check_property_catches_exception():
    def divide(a, b):
        return a / b
    with pytest.raises(PropertyFailure):
        check_property(divide, integers(-10, 10), integers(-3, 3), trials=200, seed=3)


def test_stress_brier_stays_in_bounds():
    def bounded(outcome_count, n):
        outcome = outcome_count % max(n, 2)
        n = max(n, 2)
        probs = [[1.0 / n] * n for _ in range(3)]
        outcomes = [outcome % n] * 3
        return 0.0 <= brier(probs, outcomes) <= 2.0
    assert check_property(bounded, integers(0, 5), integers(2, 6), trials=100, seed=7) == 100
