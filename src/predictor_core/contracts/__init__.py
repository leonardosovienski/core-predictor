"""predictor-core.contracts — Camada de Tipagem Pura (fachada canônica, v1.3.0).

O masterplan definitivo separa CONTRATOS (o que atravessa fronteiras) dos
MOTORES (o que calcula). Este pacote é a fachada da camada de contratos:

  contracts.points   — MarketDataPoint, SignalPoint, PredictionPoint
  contracts.registry — TrialRegistry e a governança N+1 / trava de poder

As implementações continuam onde os consumidores já as vendorizam
(`data/contracts.py`, `measurement/trials.py`) — mover o arquivo físico
quebraria os 8 vendors sem ganho; a fachada dá o caminho de import canônico
novo (`from predictor_core.contracts.points import PredictionPoint`) sem
quebrar nenhum caminho antigo. Quando os consumidores migrarem, a implementação
física pode se mudar para cá num MAJOR futuro."""

from predictor_core.contracts.collection import (  # noqa: F401
    COLLECTION_SCHEMA_VERSION,
    CollectionArchive,
    CollectionTransitionError,
    LifecycleState,
    ObservationEnvelope,
    ScientificPromotionError,
    aggregate_funnel,
)
from predictor_core.contracts.economic import (  # noqa: F401
    ECONOMIC_CONTRACT_SCHEMA_VERSION,
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
from predictor_core.contracts.points import (  # noqa: F401
    DataUnavailableError,
    MarketDataPoint,
    PredictionPoint,
    SignalPoint,
)
from predictor_core.contracts.registry import (  # noqa: F401
    MetricMismatchError,
    PowerAttestationMissingError,
    TrialRegistry,
    attestation_path_for,
    deflated_sharpe_ratio,
    load_trials,
    register_trial,
    validate_trials,
)
from predictor_core.contracts.scientific import (  # noqa: F401
    SCIENTIFIC_GOVERNANCE_SCHEMA_VERSION,
    DataAcquisitionCharter,
    DatasetFreeze,
    LatencySLA,
    ResourceBudget,
    ScientificState,
    ScientificTransitionError,
    TimestampSemantics,
    validate_scientific_transition,
)
from predictor_core.data.source_quality import (  # noqa: F401
    SourceQualityScorecard,
    SourceQualityState,
    SourceQualityThresholds,
    source_quality_scorecard,
)

# Os campos dos contratos são congelados (MappingProxyType/tuple/frozenset) e o
# json não serializa duas dessas três formas. `to_jsonable` é o caminho
# sancionado de volta para quem precisa entregar um campo de contrato ao
# json.dumps FORA do JsonlStore — que resolve o caso internamente, mas só
# para si.
from predictor_core.kernel.jsonable import to_jsonable  # noqa: F401

__all__ = [
    "MarketDataPoint",
    "SignalPoint",
    "PredictionPoint",
    "DataUnavailableError",
    "TrialRegistry",
    "register_trial",
    "load_trials",
    "validate_trials",
    "deflated_sharpe_ratio",
    "attestation_path_for",
    "PowerAttestationMissingError",
    "MetricMismatchError",
    "COLLECTION_SCHEMA_VERSION",
    "LifecycleState",
    "ObservationEnvelope",
    "CollectionArchive",
    "CollectionTransitionError",
    "ScientificPromotionError",
    "aggregate_funnel",
    "SCIENTIFIC_GOVERNANCE_SCHEMA_VERSION",
    "DataAcquisitionCharter",
    "DatasetFreeze",
    "TimestampSemantics",
    "LatencySLA",
    "ResourceBudget",
    "ScientificState",
    "ScientificTransitionError",
    "validate_scientific_transition",
    "SourceQualityScorecard",
    "SourceQualityState",
    "SourceQualityThresholds",
    "source_quality_scorecard",
    "to_jsonable",
    "ECONOMIC_CONTRACT_SCHEMA_VERSION",
    "Selection",
    "Market",
    "OutcomeProbability",
    "ProbabilisticForecast",
    "QuoteSide",
    "MarketQuote",
    "DecisionAction",
    "EconomicChainError",
    "EconomicDecision",
    "Fill",
    "ExecutionStatus",
    "ExecutionRecord",
    "SettlementStatus",
    "SettlementRecord",
    "validate_economic_chain",
]
