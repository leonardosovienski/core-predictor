"""nullref — a 3ª lente: o seletor está na cauda da distribuição de seletores aleatórios?"""
import pytest

from predictor_core.measurement.nullref import (
    random_portfolio_sequence, null_distribution, tail_probability, percentile_of,
)

UNIVERSE = list(range(100))


def _mean(sel):
    return sum(sel) / len(sel)


# --- sequência com turnover controlado -------------------------------------

def test_sequence_shapes_and_uniqueness():
    seqs = random_portfolio_sequence(range(30), n_positions=10, n_periods=5,
                                     turnover=0.2, seed=1)
    assert len(seqs) == 5
    assert all(len(s) == 10 and len(set(s)) == 10 for s in seqs)


def test_turnover_is_exactly_realized():
    # turnover 0.2, 10 posições → mantém 8, troca 2 → overlap consecutivo == 8
    seqs = random_portfolio_sequence(range(50), n_positions=10, n_periods=6,
                                     turnover=0.2, seed=3)
    for a, b in zip(seqs, seqs[1:]):
        assert len(set(a) & set(b)) == 8


def test_turnover_zero_is_buy_and_hold():
    seqs = random_portfolio_sequence(range(30), n_positions=10, n_periods=4,
                                     turnover=0.0, seed=2)
    assert all(set(s) == set(seqs[0]) for s in seqs)   # carteira nunca muda


def test_turnover_full_has_no_overlap():
    seqs = random_portfolio_sequence(range(40), n_positions=10, n_periods=3,
                                     turnover=1.0, seed=4)
    for a, b in zip(seqs, seqs[1:]):
        assert len(set(a) & set(b)) == 0


def test_sequence_rejects_small_universe():
    with pytest.raises(ValueError):
        random_portfolio_sequence(range(12), n_positions=10, n_periods=2,
                                  turnover=1.0, seed=0)   # precisa de 20, tem 12


def test_deterministic_by_seed():
    a = random_portfolio_sequence(range(30), 10, 4, 0.3, seed=7)
    b = random_portfolio_sequence(range(30), 10, 4, 0.3, seed=7)
    assert a == b


# --- distribuição nula + p-valor de posição --------------------------------

def test_skilled_selector_lands_in_upper_tail():
    null = null_distribution(_mean, UNIVERSE, n_positions=10, n_samples=2000, seed=0)
    top = _mean(list(range(90, 100)))           # seletor que pega os 10 maiores
    assert tail_probability(top, null, side="upper") < 0.01   # quase ninguém alcança


def test_random_selector_lands_in_the_middle():
    null = null_distribution(_mean, UNIVERSE, n_positions=10, n_samples=2000, seed=0)
    median_null = null[len(null) // 2]
    p = tail_probability(median_null, null, side="upper")
    assert 0.4 < p < 0.6                         # no miolo, não na cauda


def test_percentile_monotonic():
    null = null_distribution(_mean, UNIVERSE, n_positions=10, n_samples=1000, seed=1)
    assert percentile_of(min(null) - 1, null) == 0.0
    assert percentile_of(max(null) + 1, null) == 1.0


def test_tail_probability_empty_is_nan():
    import math
    assert math.isnan(tail_probability(1.0, []))
