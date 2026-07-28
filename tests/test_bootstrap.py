"""bootstrap — família unificada: schemes, guards e a invariância do cluster."""
import math

import pytest

from predictor_core.measurement.bootstrap import bootstrap_ci


def _mean(u):
    return sum(u) / len(u)


# --- schemes básicos --------------------------------------------------------

def test_iid_brackets_mean():
    data = [0.01 * i for i in range(-50, 51)]      # média ~0
    lo, hi, dist = bootstrap_ci(data, _mean, scheme="iid", n_boot=2000, seed=1)
    assert lo < sum(data) / len(data) < hi and len(dist) > 0


def test_moving_brackets_mean_autocorrelated():
    series = [math.sin(i / 3.0) for i in range(120)]
    lo, hi, dist = bootstrap_ci(series, _mean, scheme="moving",
                                block_length=10, n_boot=1000, seed=7)
    assert math.isfinite(lo) and math.isfinite(hi) and lo <= hi and dist


def test_stationary_runs_and_brackets():
    series = [math.sin(i / 4.0) for i in range(120)]
    lo, hi, _ = bootstrap_ci(series, _mean, scheme="stationary",
                             block_length=8, n_boot=1000, seed=3)
    assert lo <= _mean(series) <= hi


# --- guards ------------------------------------------------------------------

def test_unknown_scheme_raises():
    with pytest.raises(ValueError):
        bootstrap_ci([1, 2, 3], _mean, scheme="bogus")


def test_block_requires_min_length():
    with pytest.raises(ValueError):
        bootstrap_ci([1, 2, 3], _mean, scheme="moving", block_length=21)


def test_cluster_requires_key():
    with pytest.raises(ValueError):
        bootstrap_ci([1, 2, 3], _mean, scheme="cluster")


def test_nonfinite_resamples_dropped():
    lo, hi, dist = bootstrap_ci(list(range(60)), lambda u: float("inf"),
                                scheme="moving", block_length=10, n_boot=200, seed=3)
    assert (lo, hi, dist) == (None, None, [])


# --- invariância do cluster -------------------------------------------------

def test_cluster_widens_ci_under_intra_cluster_correlation():
    """Unidades perfeitamente correlacionadas dentro do cluster: o bootstrap iid
    trata cada uma como independente e SUBESTIMA a variância; o cluster reamostra o
    grupo inteiro e captura a correlação → IC do cluster mais LARGO. É a razão de o
    cluster existir (as 3 pernas do 1X2 do mesmo jogo não são 3 evidências)."""
    # 40 clusters de 5 unidades; todas as 5 iguais ao valor do cluster (corr intra = 1)
    cluster_vals = [((-1) ** k) * (1 + (k % 7)) for k in range(40)]
    series = [(v, k) for k, v in enumerate(cluster_vals) for _ in range(5)]
    stat = lambda u: sum(x[0] for x in u) / len(u)
    lo_i, hi_i, _ = bootstrap_ci(series, stat, scheme="iid", n_boot=3000, seed=11)
    lo_c, hi_c, _ = bootstrap_ci(series, stat, scheme="cluster",
                                 cluster_key=lambda x: x[1], n_boot=3000, seed=11)
    assert (hi_c - lo_c) > (hi_i - lo_i)


def test_cluster_singleton_brackets_mean():
    # 1 unidade por cluster: degenera no iid (estatisticamente) e cobre a média
    data = [0.01 * i for i in range(-40, 41)]
    series = [(v, i) for i, v in enumerate(data)]
    lo, hi, _ = bootstrap_ci(series, lambda u: sum(x[0] for x in u) / len(u),
                             scheme="cluster", cluster_key=lambda x: x[1],
                             n_boot=2000, seed=5)
    assert lo < sum(data) / len(data) < hi


def test_bootstrap_ci_serie_vazia_e_valueerror_explicito():
    """Regressão: série vazia vazava ZeroDivisionError de dentro da statistic."""
    with pytest.raises(ValueError, match="vazia"):
        bootstrap_ci([], lambda u: sum(u) / len(u), scheme="iid")
