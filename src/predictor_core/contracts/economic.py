"""Contratos econômicos neutros para mercados de resultados discretos.

O módulo descreve a fronteira comum forecast → quote → decisão → execução
→ settlement. Ele deliberadamente não decide stake, Kelly, limites de capital,
aprovações ou regras específicas de uma casa/exchange.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from predictor_core.kernel.timeindex import NaiveDatetimeError, to_utc

ECONOMIC_CONTRACT_SCHEMA_VERSION = "1.0.0"
PROBABILITY_TOLERANCE = 1e-9


def _utc_datetime(value: datetime, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be a timezone-aware datetime")
    try:
        return to_utc(value)
    except NaiveDatetimeError as exc:
        raise ValueError(f"{field} must be timezone-aware") from exc


def _required(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")


def _finite(value: float, field: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field} must be finite")
    return number


def _non_negative(value: float, field: str) -> float:
    number = _finite(value, field)
    if number < 0:
        raise ValueError(f"{field} must be non-negative")
    return number


def _probability(value: float, field: str) -> float:
    number = _finite(value, field)
    if not 0 <= number <= 1:
        raise ValueError(f"{field} must be between 0 and 1")
    return number


class QuoteSide(StrEnum):
    BACK = "back"
    LAY = "lay"


class DecisionAction(StrEnum):
    BACK = "back"
    LAY = "lay"
    PASS = "pass"


class ExecutionStatus(StrEnum):
    PENDING = "pending"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class SettlementStatus(StrEnum):
    WON = "won"
    LOST = "lost"
    PUSH = "push"
    VOID = "void"


@dataclass(frozen=True)
class Selection:
    """Uma alternativa negociável ligada a exatamente um outcome do forecast."""

    selection_id: str
    outcome_id: str
    name: str

    def __post_init__(self) -> None:
        for field in ("selection_id", "outcome_id", "name"):
            _required(getattr(self, field), f"Selection.{field}")


@dataclass(frozen=True)
class Market:
    """Identidade econômica comum; taxonomias de domínio ficam em ``market_type``."""

    market_id: str
    event_id: str
    market_type: str
    selections: tuple[Selection, ...]

    def __post_init__(self) -> None:
        for field in ("market_id", "event_id", "market_type"):
            _required(getattr(self, field), f"Market.{field}")
        selections = tuple(self.selections)
        if len(selections) < 2:
            raise ValueError("Market.selections must contain at least two selections")
        ids = [selection.selection_id for selection in selections]
        outcomes = [selection.outcome_id for selection in selections]
        if len(ids) != len(set(ids)) or len(outcomes) != len(set(outcomes)):
            raise ValueError("Market selection_id and outcome_id values must be unique")
        object.__setattr__(self, "selections", selections)


@dataclass(frozen=True)
class OutcomeProbability:
    outcome_id: str
    probability: float
    lower: float | None = None
    upper: float | None = None

    def __post_init__(self) -> None:
        _required(self.outcome_id, "OutcomeProbability.outcome_id")
        probability = _probability(self.probability, "OutcomeProbability.probability")
        lower = probability if self.lower is None else _probability(self.lower, "lower")
        upper = probability if self.upper is None else _probability(self.upper, "upper")
        if not lower <= probability <= upper:
            raise ValueError("OutcomeProbability requires lower <= probability <= upper")
        object.__setattr__(self, "probability", probability)
        object.__setattr__(self, "lower", lower)
        object.__setattr__(self, "upper", upper)


@dataclass(frozen=True)
class ProbabilisticForecast:
    """Distribuição completa e auditável emitida antes da maturação."""

    forecast_id: str
    market_id: str
    predicted_at: datetime
    matures_at: datetime
    outcomes: tuple[OutcomeProbability, ...]
    strategy_id: str
    dataset_id: str
    model_id: str
    information_cutoff: datetime

    def __post_init__(self) -> None:
        for field in ("forecast_id", "market_id", "strategy_id", "dataset_id", "model_id"):
            _required(getattr(self, field), f"ProbabilisticForecast.{field}")
        predicted_at = _utc_datetime(self.predicted_at, "ProbabilisticForecast.predicted_at")
        matures_at = _utc_datetime(self.matures_at, "ProbabilisticForecast.matures_at")
        cutoff = _utc_datetime(self.information_cutoff, "ProbabilisticForecast.information_cutoff")
        if cutoff > predicted_at:
            raise ValueError("information_cutoff cannot be after predicted_at")
        if matures_at < predicted_at:
            raise ValueError("matures_at cannot be before predicted_at")
        outcomes = tuple(self.outcomes)
        if len(outcomes) < 2:
            raise ValueError("ProbabilisticForecast requires at least two outcomes")
        ids = [outcome.outcome_id for outcome in outcomes]
        if len(ids) != len(set(ids)):
            raise ValueError("ProbabilisticForecast outcome_id values must be unique")
        if not math.isclose(
            sum(outcome.probability for outcome in outcomes),
            1.0,
            rel_tol=0.0,
            abs_tol=PROBABILITY_TOLERANCE,
        ):
            raise ValueError("ProbabilisticForecast outcome probabilities must sum to 1")
        object.__setattr__(self, "predicted_at", predicted_at)
        object.__setattr__(self, "matures_at", matures_at)
        object.__setattr__(self, "information_cutoff", cutoff)
        object.__setattr__(self, "outcomes", outcomes)

    def probability_for(self, outcome_id: str) -> float:
        for outcome in self.outcomes:
            if outcome.outcome_id == outcome_id:
                return outcome.probability
        raise KeyError(outcome_id)


@dataclass(frozen=True)
class MarketQuote:
    """Snapshot temporal de preço e liquidez efetivamente disponíveis."""

    quote_id: str
    market_id: str
    selection_id: str
    source: str
    side: QuoteSide
    decimal_odds: float
    available_size: float
    currency: str
    quoted_at: datetime
    published_at: datetime
    ingested_at: datetime
    line: float | None = None
    spread: float | None = None
    commission_rate: float = 0.0
    is_closing: bool = False

    def __post_init__(self) -> None:
        for field in ("quote_id", "market_id", "selection_id", "source", "currency"):
            _required(getattr(self, field), f"MarketQuote.{field}")
        try:
            side = QuoteSide(self.side)
        except ValueError as exc:
            raise ValueError("MarketQuote.side must be 'back' or 'lay'") from exc
        odds = _finite(self.decimal_odds, "MarketQuote.decimal_odds")
        if odds <= 1:
            raise ValueError("MarketQuote.decimal_odds must be greater than 1")
        available = _non_negative(self.available_size, "MarketQuote.available_size")
        commission = _probability(self.commission_rate, "MarketQuote.commission_rate")
        quoted_at = _utc_datetime(self.quoted_at, "MarketQuote.quoted_at")
        published_at = _utc_datetime(self.published_at, "MarketQuote.published_at")
        ingested_at = _utc_datetime(self.ingested_at, "MarketQuote.ingested_at")
        if not quoted_at <= published_at <= ingested_at:
            raise ValueError("MarketQuote requires quoted_at <= published_at <= ingested_at")
        object.__setattr__(self, "side", side)
        object.__setattr__(self, "decimal_odds", odds)
        object.__setattr__(self, "available_size", available)
        object.__setattr__(self, "commission_rate", commission)
        object.__setattr__(self, "quoted_at", quoted_at)
        object.__setattr__(self, "published_at", published_at)
        object.__setattr__(self, "ingested_at", ingested_at)
        if self.line is not None:
            object.__setattr__(self, "line", _finite(self.line, "MarketQuote.line"))
        if self.spread is not None:
            object.__setattr__(self, "spread", _non_negative(self.spread, "MarketQuote.spread"))

    @property
    def implied_probability(self) -> float:
        return 1.0 / self.decimal_odds


@dataclass(frozen=True)
class EconomicDecision:
    """Decisão registrada; a política que a produziu permanece fora do Core."""

    decision_id: str
    forecast_id: str
    quote_id: str
    decided_at: datetime
    action: DecisionAction
    estimated_probability: float
    estimated_edge: float
    requested_size: float
    economically_eligible: bool
    eligibility_reason: str = ""

    def __post_init__(self) -> None:
        for field in ("decision_id", "forecast_id", "quote_id"):
            _required(getattr(self, field), f"EconomicDecision.{field}")
        action = DecisionAction(self.action)
        size = _non_negative(self.requested_size, "EconomicDecision.requested_size")
        probability = _probability(self.estimated_probability, "estimated_probability")
        edge = _finite(self.estimated_edge, "EconomicDecision.estimated_edge")
        if action is DecisionAction.PASS and size != 0:
            raise ValueError("PASS decisions must have requested_size=0")
        if not self.economically_eligible and not self.eligibility_reason.strip():
            raise ValueError("ineligible decisions require eligibility_reason")
        if not self.economically_eligible and (action is not DecisionAction.PASS or size != 0):
            raise ValueError("ineligible decisions must be PASS with requested_size=0")
        object.__setattr__(self, "action", action)
        object.__setattr__(self, "requested_size", size)
        object.__setattr__(self, "estimated_probability", probability)
        object.__setattr__(self, "estimated_edge", edge)
        object.__setattr__(self, "decided_at", _utc_datetime(self.decided_at, "decided_at"))


@dataclass(frozen=True)
class Fill:
    fill_id: str
    filled_at: datetime
    decimal_odds: float
    size: float
    fee: float = 0.0

    def __post_init__(self) -> None:
        _required(self.fill_id, "Fill.fill_id")
        odds = _finite(self.decimal_odds, "Fill.decimal_odds")
        if odds <= 1:
            raise ValueError("Fill.decimal_odds must be greater than 1")
        size = _finite(self.size, "Fill.size")
        if size <= 0:
            raise ValueError("Fill.size must be positive")
        object.__setattr__(self, "decimal_odds", odds)
        object.__setattr__(self, "size", size)
        object.__setattr__(self, "fee", _non_negative(self.fee, "Fill.fee"))
        object.__setattr__(self, "filled_at", _utc_datetime(self.filled_at, "Fill.filled_at"))


@dataclass(frozen=True)
class ExecutionRecord:
    execution_id: str
    decision_id: str
    submitted_at: datetime
    status: ExecutionStatus
    fills: tuple[Fill, ...] = ()
    external_order_id: str = ""

    def __post_init__(self) -> None:
        _required(self.execution_id, "ExecutionRecord.execution_id")
        _required(self.decision_id, "ExecutionRecord.decision_id")
        submitted_at = _utc_datetime(self.submitted_at, "ExecutionRecord.submitted_at")
        status = ExecutionStatus(self.status)
        fills = tuple(self.fills)
        if any(fill.filled_at < submitted_at for fill in fills):
            raise ValueError("ExecutionRecord fills cannot precede submitted_at")
        if status is ExecutionStatus.FILLED and not fills:
            raise ValueError("FILLED executions require at least one fill")
        if status in {ExecutionStatus.PENDING, ExecutionStatus.REJECTED} and fills:
            raise ValueError(f"{status.value} executions cannot contain fills")
        object.__setattr__(self, "submitted_at", submitted_at)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "fills", fills)

    @property
    def filled_size(self) -> float:
        return sum(fill.size for fill in self.fills)

    @property
    def average_odds(self) -> float | None:
        size = self.filled_size
        return None if size == 0 else sum(f.decimal_odds * f.size for f in self.fills) / size


@dataclass(frozen=True)
class SettlementRecord:
    settlement_id: str
    execution_id: str
    settled_at: datetime
    status: SettlementStatus
    gross_pnl: float
    costs: float
    net_pnl: float
    currency: str
    winning_outcome_id: str | None = None

    def __post_init__(self) -> None:
        for field in ("settlement_id", "execution_id", "currency"):
            _required(getattr(self, field), f"SettlementRecord.{field}")
        status = SettlementStatus(self.status)
        gross = _finite(self.gross_pnl, "SettlementRecord.gross_pnl")
        costs = _non_negative(self.costs, "SettlementRecord.costs")
        net = _finite(self.net_pnl, "SettlementRecord.net_pnl")
        if not math.isclose(net, gross - costs, rel_tol=1e-12, abs_tol=1e-9):
            raise ValueError("SettlementRecord requires net_pnl = gross_pnl - costs")
        if status is SettlementStatus.VOID and (gross != 0 or net != -costs):
            raise ValueError("VOID settlements cannot have non-zero gross_pnl")
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "gross_pnl", gross)
        object.__setattr__(self, "costs", costs)
        object.__setattr__(self, "net_pnl", net)
        object.__setattr__(self, "settled_at", _utc_datetime(self.settled_at, "settled_at"))


class EconomicChainError(ValueError):
    """A cadeia econômica contém referências ou tempos incompatíveis."""


def validate_economic_chain(
    market: Market,
    forecast: ProbabilisticForecast,
    quote: MarketQuote,
    decision: EconomicDecision,
    execution: ExecutionRecord,
    settlement: SettlementRecord | None = None,
) -> None:
    """Valida relações entre records sem incorporar política de risco ou capital."""

    if forecast.market_id != market.market_id or quote.market_id != market.market_id:
        raise EconomicChainError("market_id mismatch in economic chain")
    selection_by_id = {selection.selection_id: selection for selection in market.selections}
    if set(selection.outcome_id for selection in market.selections) != set(
        outcome.outcome_id for outcome in forecast.outcomes
    ):
        raise EconomicChainError("forecast outcomes must match market selections")
    if quote.selection_id not in selection_by_id:
        raise EconomicChainError("quote selection_id is not part of market")
    if decision.forecast_id != forecast.forecast_id or decision.quote_id != quote.quote_id:
        raise EconomicChainError("decision references do not match forecast and quote")
    if execution.decision_id != decision.decision_id:
        raise EconomicChainError("execution decision_id does not match decision")
    if not forecast.predicted_at <= quote.published_at <= decision.decided_at:
        raise EconomicChainError("quote must be available after forecast and before decision")
    if decision.decided_at >= forecast.matures_at:
        raise EconomicChainError("decision must precede forecast maturation")
    if execution.submitted_at < decision.decided_at:
        raise EconomicChainError("execution cannot be submitted before decision")
    expected_action = DecisionAction(quote.side.value)
    if decision.action is not DecisionAction.PASS and decision.action is not expected_action:
        raise EconomicChainError("decision action must match quote side")
    selection = selection_by_id[quote.selection_id]
    expected_probability = forecast.probability_for(selection.outcome_id)
    if not math.isclose(
        decision.estimated_probability,
        expected_probability,
        rel_tol=0.0,
        abs_tol=PROBABILITY_TOLERANCE,
    ):
        raise EconomicChainError("decision probability must match selected forecast outcome")
    if execution.filled_size > decision.requested_size + PROBABILITY_TOLERANCE:
        raise EconomicChainError("filled size cannot exceed requested size")
    if settlement is None:
        return
    if settlement.execution_id != execution.execution_id:
        raise EconomicChainError("settlement execution_id does not match execution")
    last_execution_at = max(
        (fill.filled_at for fill in execution.fills), default=execution.submitted_at
    )
    if settlement.settled_at < last_execution_at:
        raise EconomicChainError("settlement cannot precede execution")
    outcome_ids = {outcome.outcome_id for outcome in forecast.outcomes}
    if settlement.winning_outcome_id is not None:
        if settlement.winning_outcome_id not in outcome_ids:
            raise EconomicChainError("winning_outcome_id is not part of forecast")
    elif settlement.status in {SettlementStatus.WON, SettlementStatus.LOST}:
        raise EconomicChainError("won/lost settlement requires winning_outcome_id")


__all__ = [
    "ECONOMIC_CONTRACT_SCHEMA_VERSION",
    "DecisionAction",
    "EconomicDecision",
    "EconomicChainError",
    "ExecutionRecord",
    "ExecutionStatus",
    "Fill",
    "Market",
    "MarketQuote",
    "OutcomeProbability",
    "ProbabilisticForecast",
    "QuoteSide",
    "Selection",
    "SettlementRecord",
    "SettlementStatus",
    "validate_economic_chain",
]
