"""measurement.calibration — Platt corrige miscalibração conhecida; Shin remove vig."""

import random

import pytest

from predictor_core.measurement.calibration import PlattCalibrator, shin_devig
from predictor_core.measurement.metrics import log_loss


def _sigmoid(x):
    import math

    return 1.0 / (1.0 + math.exp(-x))


def test_platt_improves_overconfident_predictor():
    # Verdade: p_true; previsor superconfiante: empurra p para os extremos.
    rng = random.Random(1)
    p_true = [rng.uniform(0.2, 0.8) for _ in range(400)]
    outcomes = [1 if rng.random() < p else 0 for p in p_true]
    import math

    overconfident = [_sigmoid(3.0 * math.log(p / (1 - p))) for p in p_true]

    cal = PlattCalibrator().fit(overconfident, outcomes)
    calibrated = cal.transform(overconfident)
    ll_before = log_loss([[1 - p, p] for p in overconfident], outcomes)
    ll_after = log_loss([[1 - p, p] for p in calibrated], outcomes)
    assert ll_after < ll_before


def test_platt_transform_before_fit_raises():
    with pytest.raises(RuntimeError):
        PlattCalibrator().transform([0.5])


def test_platt_is_callable_decorator():
    cal = PlattCalibrator().fit([0.3, 0.7, 0.4, 0.8], [0, 1, 0, 1])
    assert cal([0.5]) == cal.transform([0.5])


def test_shin_devig_sums_to_one_and_preserves_order():
    implied = [1 / 1.90, 1 / 3.50, 1 / 4.20]  # booksum > 1 (margem)
    clean = shin_devig(implied)
    assert sum(clean) == pytest.approx(1.0)
    assert clean[0] > clean[1] > clean[2]
    assert all(0 < p < 1 for p in clean)


def test_shin_devig_no_margin_is_proportional():
    clean = shin_devig([0.6, 0.4])
    assert clean == pytest.approx([0.6, 0.4])


def test_shin_devig_shrinks_longshot_more_than_proportional():
    # Propriedade central do Shin: o azarão é mais inflado pelo vig do que o
    # favorito — o de-vig de Shin devolve p_azarão MENOR que a normalização simples.
    implied = [1 / 1.15, 1 / 6.00]  # booksum ≈ 1.036 — margem real
    booksum = sum(implied)
    proportional = [p / booksum for p in implied]
    shin = shin_devig(implied)
    assert shin[1] < proportional[1]
    assert shin[0] > proportional[0]


def test_shin_devig_rejects_bad_input():
    with pytest.raises(ValueError):
        shin_devig([0.9])
    with pytest.raises(ValueError):
        shin_devig([0.5, 0.0])
