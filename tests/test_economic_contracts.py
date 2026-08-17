from datetime import UTC, datetime, timedelta

import pytest

from predictor_core import (
    DecisionAction,
    EconomicChainError,
    EconomicDecision,
    ExecutionRecord,
    ExecutionStatus,
    Fill,
    Market,
    MarketQuote,
    OutcomeProbability,
    ProbabilisticForecast,
    QuoteSide,
    Selection,
    SettlementRecord,
    SettlementStatus,
    validate_economic_chain,
)

T0 = datetime(2026, 8, 17, 12, tzinfo=UTC)


def forecast(**changes):
    values = dict(
        forecast_id="fc-1",
        market_id="match-winner-1",
        predicted_at=T0,
        matures_at=T0 + timedelta(hours=3),
        outcomes=(OutcomeProbability("home", 0.6, 0.55, 0.65), OutcomeProbability("away", 0.4)),
        strategy_id="value-v3",
        dataset_id="dataset-sha256:abc",
        model_id="model-sha256:def",
        information_cutoff=T0 - timedelta(minutes=1),
    )
    values.update(changes)
    return ProbabilisticForecast(**values)


def quote(**changes):
    values = dict(
        quote_id="q-1",
        market_id="match-winner-1",
        selection_id="home",
        source="exchange-a",
        side=QuoteSide.BACK,
        decimal_odds=2.0,
        available_size=100.0,
        currency="BRL",
        quoted_at=T0,
        published_at=T0 + timedelta(seconds=1),
        ingested_at=T0 + timedelta(seconds=2),
    )
    values.update(changes)
    return MarketQuote(**values)


def test_market_has_domain_neutral_identity_and_unique_selections():
    market = Market(
        "m1",
        "event-1",
        "winner",
        (Selection("s1", "home", "Casa"), Selection("s2", "away", "Fora")),
    )
    assert market.selections[0].outcome_id == "home"
    with pytest.raises(ValueError, match="unique"):
        Market("m1", "e1", "winner", (Selection("s1", "x", "X"), Selection("s1", "y", "Y")))


def test_forecast_is_complete_normalized_and_temporally_safe():
    item = forecast()
    assert item.probability_for("home") == 0.6
    assert item.outcomes[1].lower == item.outcomes[1].probability
    with pytest.raises(ValueError, match="sum to 1"):
        forecast(outcomes=(OutcomeProbability("a", 0.8), OutcomeProbability("b", 0.3)))
    with pytest.raises(ValueError, match="information_cutoff"):
        forecast(information_cutoff=T0 + timedelta(seconds=1))


def test_quote_exposes_executable_price_liquidity_and_temporal_provenance():
    item = quote(line=-1.5, spread=0.05, commission_rate=0.02, is_closing=True)
    assert item.implied_probability == 0.5
    assert item.side is QuoteSide.BACK
    assert item.is_closing
    with pytest.raises(ValueError, match="quoted_at <= published_at <= ingested_at"):
        quote(ingested_at=T0)


def test_decision_records_eligibility_without_embedding_risk_policy():
    item = EconomicDecision("d1", "fc-1", "q-1", T0, DecisionAction.BACK, 0.6, 0.2, 25.0, True)
    assert item.requested_size == 25
    with pytest.raises(ValueError, match="eligibility_reason"):
        EconomicDecision("d2", "f", "q", T0, "pass", 0.5, 0, 0, False)
    with pytest.raises(ValueError, match="requested_size=0"):
        EconomicDecision("d3", "f", "q", T0, "pass", 0.5, 0, 1, True)


def test_execution_aggregates_partial_fills():
    fills = (
        Fill("f1", T0 + timedelta(seconds=2), 2.0, 10, 0.1),
        Fill("f2", T0 + timedelta(seconds=3), 2.2, 5),
    )
    record = ExecutionRecord("e1", "d1", T0, ExecutionStatus.FILLED, fills)
    assert record.filled_size == 15
    assert record.average_odds == pytest.approx((20 + 11) / 15)
    with pytest.raises(ValueError, match="require at least one fill"):
        ExecutionRecord("e2", "d2", T0, "filled")


def test_settlement_reconciles_costs_and_net_pnl():
    record = SettlementRecord("s1", "e1", T0, SettlementStatus.WON, 10.0, 0.5, 9.5, "BRL", "home")
    assert record.net_pnl == 9.5
    with pytest.raises(ValueError, match="net_pnl = gross_pnl - costs"):
        SettlementRecord("s2", "e2", T0, "lost", -10, 1, -10, "BRL")


def test_complete_economic_chain_validates_cross_record_references_and_time():
    market = Market(
        "match-winner-1",
        "event-1",
        "winner",
        (Selection("home", "home", "Home"), Selection("away", "away", "Away")),
    )
    fc = forecast()
    market_quote = quote()
    decision = EconomicDecision(
        "d1",
        "fc-1",
        "q-1",
        T0 + timedelta(seconds=3),
        "back",
        0.6,
        0.2,
        10,
        True,
    )
    fill = Fill("fill-1", T0 + timedelta(seconds=5), 2.0, 10, 0.1)
    execution = ExecutionRecord(
        "execution-1",
        "d1",
        T0 + timedelta(seconds=4),
        "filled",
        (fill,),
    )
    settlement = SettlementRecord(
        "settlement-1",
        "execution-1",
        T0 + timedelta(hours=4),
        "won",
        10,
        0.5,
        9.5,
        "BRL",
        "home",
    )
    assert (
        validate_economic_chain(market, fc, market_quote, decision, execution, settlement) is None
    )
    with pytest.raises(EconomicChainError, match="market_id mismatch"):
        validate_economic_chain(
            Market("other", "event-1", "winner", market.selections),
            fc,
            market_quote,
            decision,
            execution,
        )
