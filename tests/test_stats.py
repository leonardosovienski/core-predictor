"""stats — onde um bug é silencioso e caro (significância fabricada, drawdown colapsado)."""

import math

import pytest

from predictor_core import stats

# --- spearman -------------------------------------------------------------


def test_spearman_perfect_monotonic():
    assert stats.spearman([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)
    assert stats.spearman([1, 2, 3, 4], [40, 30, 20, 10]) == pytest.approx(-1.0)


def test_spearman_none_when_undefined():
    assert stats.spearman([1, 2], [1, 2]) is None  # n < 3
    assert stats.spearman([1, 1, 1, 1], [1, 2, 3, 4]) is None  # variância nula


# --- ci_mean --------------------------------------------------------------


def test_ci_mean_brackets_the_mean():
    data = [0.01 * i for i in range(-50, 51)]  # média ~0
    with pytest.warns(DeprecationWarning):
        lo, hi = stats.ci_mean(data, n_boot=2000, seed=1)
    assert lo < sum(data) / len(data) < hi


# --- block_bootstrap_ci ---------------------------------------------------


def test_block_bootstrap_brackets_mean_and_is_finite():
    series = [math.sin(i / 3.0) for i in range(120)]  # autocorrelacionada
    with pytest.warns(DeprecationWarning):
        lo, hi, dist = stats.block_bootstrap_ci(
            series, lambda u: sum(u) / len(u), block_length=10, n_boot=1000, seed=7
        )
    assert math.isfinite(lo) and math.isfinite(hi) and lo <= hi
    assert len(dist) > 0


def test_block_bootstrap_drops_nonfinite_resamples():
    # statistic sempre infinita → todas descartadas → (None, None, [])
    series = list(range(60))
    with pytest.warns(DeprecationWarning):
        lo, hi, dist = stats.block_bootstrap_ci(
            series, lambda u: float("inf"), block_length=10, n_boot=200, seed=3
        )
    assert (lo, hi, dist) == (None, None, [])


def test_block_bootstrap_requires_min_length():
    with pytest.warns(DeprecationWarning), pytest.raises(ValueError):
        stats.block_bootstrap_ci([1, 2, 3], lambda u: sum(u), block_length=21)


def test_spearman_block_ci_returns_triple():
    pairs = [(i, i + (i % 5) - 2) for i in range(40)]  # positiva, com ruído
    rho, lo, hi = stats.spearman_block_ci(pairs, n_boot=500, seed=5)
    assert rho is not None and lo <= hi and rho > 0  # IC ordenado; correlação positiva
    assert stats.spearman_block_ci([(1, 1), (2, 2)]) == (None, None, None)  # n < 4


# --- sharpe / sortino edge cases -----------------------------------------


def test_sharpe_constant_series_signals_direction():
    assert stats.sharpe([0.01, 0.01, 0.01]) == float("inf")
    assert stats.sharpe([-0.01, -0.01, -0.01]) == float("-inf")
    assert math.isnan(stats.sharpe([0.0, 0.0, 0.0]))


# --- max_drawdown CONTRACT (o bug medido no cripto/v3) --------------------


def test_max_drawdown_on_equity_curve():
    # pico 100 → vale 80 = 20% de drawdown
    assert stats.max_drawdown([100, 110, 88, 95, 100]) == pytest.approx(0.2)


def test_max_drawdown_raises_on_nonpositive_equity():
    # nível que toca <= 0 (sintoma de receber retornos crus em vez de equity curve)
    # → levanta, em vez de devolver 0 enganoso (o bug medido no cripto/v3)
    with pytest.raises(ValueError):
        stats.max_drawdown([0.0, -0.02, 0.03])


# --- probabilistic_sharpe_ratio ------------------------------------------


def test_psr_in_unit_interval_and_monotonic():
    fraca = [0.001 * ((i % 5) - 2) for i in range(60)]  # ~sem skill
    forte = [0.02 + 0.001 * ((i % 5) - 2) for i in range(60)]  # média positiva clara
    p_fraca = stats.probabilistic_sharpe_ratio(fraca)
    p_forte = stats.probabilistic_sharpe_ratio(forte)
    assert 0.0 <= p_fraca <= 1.0 and 0.0 <= p_forte <= 1.0
    assert p_forte > p_fraca


def test_psr_nan_for_tiny_sample():
    assert math.isnan(stats.probabilistic_sharpe_ratio([0.01, 0.02]))
