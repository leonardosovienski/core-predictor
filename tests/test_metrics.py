"""metrics — régua probabilística: previsor perfeito=0, penalidade ordinal, DM."""
import math

import pytest

from predictor_core.measurement.metrics import (
    brier, log_loss, rps, calibration_table, diebold_mariano,
)
from predictor_core.measurement.metrics import _t_two_sided_p


# --- Brier ------------------------------------------------------------------

def test_brier_perfect_is_zero():
    probs = [[1.0, 0.0, 0.0], [0.0, 0.0, 1.0]]
    assert brier(probs, [0, 2]) == pytest.approx(0.0)


def test_brier_uniform_three_classes():
    # (1/3-1)² + 2·(1/3)² = 4/9 + 2/9 = 0.6667 por observação
    probs = [[1 / 3, 1 / 3, 1 / 3]]
    assert brier(probs, [0]) == pytest.approx(0.6667, abs=1e-3)


# --- log-loss ---------------------------------------------------------------

def test_log_loss_perfect_near_zero():
    assert log_loss([[1.0, 0.0]], [0]) == pytest.approx(0.0, abs=1e-9)


def test_log_loss_penalizes_confident_wrong():
    confident_wrong = log_loss([[0.01, 0.99]], [0])
    unsure = log_loss([[0.5, 0.5]], [0])
    assert confident_wrong > unsure


# --- RPS (ordinal) ----------------------------------------------------------

def test_rps_perfect_is_zero():
    assert rps([[1.0, 0.0, 0.0]], [0]) == pytest.approx(0.0)


def test_rps_penalizes_distance_in_order():
    # resultado real = classe 0. Prever a classe 1 (vizinha) deve punir MENOS que
    # prever a classe 2 (distante) — a assinatura ordinal do RPS.
    near = rps([[0.0, 1.0, 0.0]], [0])
    far = rps([[0.0, 0.0, 1.0]], [0])
    assert far > near


def test_rps_requires_two_classes():
    with pytest.raises(ValueError):
        rps([[1.0]], [0])


# --- calibração -------------------------------------------------------------

def test_calibration_well_calibrated():
    # metade com p=0.2 (20% acertam) e metade com p=0.8 (80% acertam)
    probs = [0.2] * 100 + [0.8] * 100
    outcomes = [1] * 20 + [0] * 80 + [1] * 80 + [0] * 20
    table = calibration_table(probs, outcomes, bins=10)
    for row in table:
        assert abs(row["mean_pred"] - row["obs_freq"]) < 0.05


# --- Diebold-Mariano --------------------------------------------------------

def test_dm_t_pvalue_matches_reference():
    # t=2.0, df=10 → p bilateral ≈ 0.0734 (tabela t de Student)
    assert _t_two_sided_p(2.0, 10) == pytest.approx(0.0734, abs=1e-3)


def test_dm_detects_better_forecaster():
    # A tem perda sistematicamente menor que B. Ruído DIFERENTE em cada série (senão
    # o diferencial seria constante → variância nula → nan, que é o caso do teste abaixo).
    loss_a = [0.10 + 0.02 * math.sin(i) for i in range(60)]
    loss_b = [0.20 + 0.02 * math.cos(i) for i in range(60)]
    dm, p = diebold_mariano(loss_a, loss_b)
    assert dm < 0 and 0.0 <= p <= 1.0 and p < 0.01


def test_dm_nan_on_zero_variance():
    dm, p = diebold_mariano([0.1] * 10, [0.1] * 10)   # diferencial constante 0
    assert math.isnan(dm) and math.isnan(p)
