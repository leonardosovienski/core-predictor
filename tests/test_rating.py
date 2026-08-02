"""kernel.rating — EloEngine generalizado: expectativa simétrica, soma-zero, ranking multi-N."""

import pytest

from predictor_core.kernel.rating import RatingBook, expected_score, update_pair


def test_expected_score_symmetric():
    a, b = expected_score(1600, 1400), expected_score(1400, 1600)
    assert a + b == pytest.approx(1.0)
    assert a > 0.5


def test_expected_score_equal_ratings_is_half():
    assert expected_score(1500, 1500) == pytest.approx(0.5)


def test_update_pair_zero_sum_delta():
    new_a, new_b = update_pair(1500, 1500, 1.0, k=32)
    assert (new_a - 1500) == pytest.approx(-(new_b - 1500))
    assert new_a > 1500 > new_b


def test_update_pair_rejects_invalid_score():
    with pytest.raises(ValueError):
        update_pair(1500, 1500, 1.5)


def test_rating_book_record_match_updates_both():
    book = RatingBook()
    ea, eb = book.record_match("messi", "mbappe", score_a=1.0)
    assert ea.rating > 1500 > eb.rating
    assert ea.games == 1 and eb.games == 1
    assert book.rating("messi") == ea.rating


def test_rating_book_record_ranking_orders_by_strength():
    book = RatingBook()
    book.record_ranking(["p1", "p2", "p3"])
    r1, r2, r3 = book.rating("p1"), book.rating("p2"), book.rating("p3")
    assert r1 > r2 > r3


def test_rating_book_record_ranking_requires_two():
    book = RatingBook()
    with pytest.raises(ValueError):
        book.record_ranking(["solo"])


def test_record_ranking_k_factor_recebe_a_mesma_escala():
    """Regressão: k_factor ignorava a divisão K/(N-1) — corrida de N movia o
    rating N-1x mais com callback do que com K fixo equivalente."""
    fixo = RatingBook(k=32.0)
    fixo.record_ranking(["a", "b", "c", "d", "e"])
    dinamico = RatingBook(k=32.0, k_factor=lambda e: 32.0)
    dinamico.record_ranking(["a", "b", "c", "d", "e"])
    assert dinamico.rating("a") == pytest.approx(fixo.rating("a"))
    assert dinamico.rating("e") == pytest.approx(fixo.rating("e"))


def test_record_ranking_restaura_k_factor_apos_rodar():
    cb = lambda e: 40.0
    book = RatingBook(k=32.0, k_factor=cb)
    book.record_ranking(["a", "b"])
    assert book.k_factor is cb and book.k == 32.0


def test_record_ranking_rejeita_nome_duplicado():
    # Regressão (auditoria hostil 2026-07-17): nome repetido gerava um
    # confronto "entidade contra si mesma" (mesmo objeto de estado nos dois
    # lados), inflando games e descontando o rating do adversário comum duas
    # vezes contra a mesma pessoa, sem nenhum erro.
    book = RatingBook()
    with pytest.raises(ValueError, match="únicos"):
        book.record_ranking(["alice", "alice", "bob"])
