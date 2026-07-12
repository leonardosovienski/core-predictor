"""kernel.rating — EloEngine generalizado: expectativa simétrica, soma-zero, ranking multi-N."""
import pytest

from predictor_core.kernel.rating import Entity, RatingBook, expected_score, update_pair


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
