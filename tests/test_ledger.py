"""ledger — partida dobrada: toda transação soma zero, saldos são exatos."""
from datetime import datetime, timezone

import pytest

from predictor_core.measurement.ledger import Ledger, Posting, Transaction, UnbalancedTransactionError


def _now():
    return datetime(2026, 7, 11, tzinfo=timezone.utc)


def test_balanced_transaction_ok():
    txn = Transaction(at=_now(), postings=(Posting("assets:btc", 10.0), Posting("equity:pnl", -10.0)))
    assert txn.postings[0].amount == 10.0


def test_unbalanced_transaction_raises():
    with pytest.raises(UnbalancedTransactionError):
        Transaction(at=_now(), postings=(Posting("assets:btc", 10.0), Posting("equity:pnl", -9.0)))


def test_single_posting_raises():
    with pytest.raises(ValueError):
        Transaction(at=_now(), postings=(Posting("assets:btc", 0.0),))


def test_ledger_post_and_balance():
    ledger = Ledger()
    ledger.post(_now(), [Posting("assets:btc", 10.0), Posting("equity:pnl", -10.0)], narration="stake")
    ledger.post(_now(), [Posting("assets:btc", -3.0), Posting("equity:pnl", 3.0)], narration="loss")
    assert ledger.balance("assets:btc") == pytest.approx(7.0)
    assert ledger.balance("equity:pnl") == pytest.approx(-7.0)


def test_ledger_balances_all_accounts():
    ledger = Ledger()
    ledger.post(_now(), [Posting("a", 5.0), Posting("b", -5.0)])
    bals = ledger.balances()
    assert bals == {"a": 5.0, "b": -5.0}


def test_ledger_history_filters_by_account():
    ledger = Ledger()
    t1 = ledger.post(_now(), [Posting("a", 5.0), Posting("b", -5.0)])
    ledger.post(_now(), [Posting("c", 1.0), Posting("d", -1.0)])
    assert ledger.history("a") == [t1]
    assert ledger.history("z") == []


def test_posting_rejects_nonfinite_amount():
    with pytest.raises(ValueError):
        Posting("a", float("nan"))
