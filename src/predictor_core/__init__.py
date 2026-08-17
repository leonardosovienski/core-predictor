"""predictor-core — biblioteca científica canônica instalada como distribuição.

Estrutura em camadas: kernel (L0) · measurement (L1) · data (L2, futuro). A API pública
estável é re-exportada aqui — `from predictor_core import sharpe, emit_event, replay`.
Os caminhos por submódulo (`predictor_core.measurement.stats`, ...) são o destino
canônico; os módulos planos de topo (`predictor_core.stats`, ...) são shims de compat.
"""

from importlib.metadata import version

__version__ = version("predictor-core")

# --- API pública estável (re-export das camadas) ---------------------------
from predictor_core.contracts.economic import (
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
from predictor_core.contracts.scientific import (
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
from predictor_core.data.asof import state_asof
from predictor_core.data.collection import (
    COLLECTION_SCHEMA_VERSION,
    CollectionArchive,
    CollectionTransitionError,
    LifecycleState,
    ObservationEnvelope,
    ScientificPromotionError,
    aggregate_funnel,
)
from predictor_core.data.contracts import PredictionPoint
from predictor_core.data.source_quality import (
    SourceQualityScorecard,
    SourceQualityState,
    SourceQualityThresholds,
    source_quality_scorecard,
)
from predictor_core.kernel.infra import config_hash, connect, run_migrations
from predictor_core.kernel.jsonl_store import JsonlStore
from predictor_core.kernel.meta import StaleModelError, fingerprint, validate
from predictor_core.kernel.net import download_file, sha256_file
from predictor_core.kernel.obs import emit_event, get_logger, read_events, setup_logging
from predictor_core.kernel.rating import Entity, RatingBook, expected_score, update_pair
from predictor_core.kernel.settings import MissingCredentialsError, require_secrets
from predictor_core.kernel.timeindex import NaiveDatetimeError, iso_z, parse_iso, to_utc, utcnow
from predictor_core.measurement.bootstrap import bootstrap_ci
from predictor_core.measurement.calibration import PlattCalibrator, shin_devig
from predictor_core.measurement.ledger import (
    Ledger,
    Posting,
    Transaction,
    UnbalancedTransactionError,
)
from predictor_core.measurement.metrics import (
    brier,
    calibration_table,
    diebold_mariano,
    log_loss,
    rps,
)
from predictor_core.measurement.nullref import (
    null_distribution,
    percentile_of,
    random_portfolio_sequence,
    tail_probability,
)
from predictor_core.measurement.ordinal import (
    fit_plackett_luce,
    plackett_luce_prob,
    rank_probabilities,
)
from predictor_core.measurement.replay import LookaheadError, PastView, replay
from predictor_core.measurement.stats import (
    block_bootstrap_ci,
    ci_mean,
    max_drawdown,
    probabilistic_sharpe_ratio,
    sharpe,
    sortino,
    spearman,  # 2 últimas: depreciadas
    spearman_block_ci,
)
from predictor_core.measurement.trials import (
    MetricMismatchError,
    PowerAttestationMissingError,
    TrialRegistry,
    attestation_path_for,
    deflated_sharpe_ratio,
    load_trials,
    register_trial,
    validate_trials,
)
from predictor_core.testing.prequential import PrequentialEvaluator
from predictor_core.testing.stress import (
    PropertyFailure,
    check_property,
    floats,
    integers,
    lists_of,
)

__all__ = [
    "__version__",
    # kernel
    "connect",
    "run_migrations",
    "config_hash",
    "emit_event",
    "read_events",
    "setup_logging",
    "get_logger",
    "require_secrets",
    "MissingCredentialsError",
    "download_file",
    "sha256_file",
    "fingerprint",
    "validate",
    "StaleModelError",
    # measurement — financeira
    "sharpe",
    "sortino",
    "max_drawdown",
    "probabilistic_sharpe_ratio",
    "spearman",
    "spearman_block_ci",
    # measurement — bootstrap (novo) + depreciados
    "bootstrap_ci",
    "block_bootstrap_ci",
    "ci_mean",
    # measurement — probabilística
    "brier",
    "log_loss",
    "rps",
    "calibration_table",
    "diebold_mariano",
    # measurement — trials/DSR (+ governança reconciliada 2026-07-09)
    "TrialRegistry",
    "register_trial",
    "load_trials",
    "validate_trials",
    "deflated_sharpe_ratio",
    "attestation_path_for",
    "PowerAttestationMissingError",
    # measurement — referência nula (3ª lente)
    "null_distribution",
    "tail_probability",
    "percentile_of",
    "random_portfolio_sequence",
    # measurement — replay
    "replay",
    "PastView",
    "LookaheadError",
    # measurement — ledger (partida dobrada, agosto/2026)
    "Posting",
    "Transaction",
    "Ledger",
    "UnbalancedTransactionError",
    # measurement — camada ordinal (Plackett-Luce, agosto/2026)
    "plackett_luce_prob",
    "fit_plackett_luce",
    "rank_probabilities",
    # kernel — EloEngine generalizado (agosto/2026)
    "Entity",
    "expected_score",
    "update_pair",
    "RatingBook",
    # testing — telemetria de estresse property-based (agosto/2026)
    "check_property",
    "floats",
    "integers",
    "lists_of",
    "PropertyFailure",
    # v1.3.0 — estado definitivo: calibração, tempo, JSONL, prequential, punição global
    "PlattCalibrator",
    "shin_devig",
    "utcnow",
    "to_utc",
    "iso_z",
    "parse_iso",
    "NaiveDatetimeError",
    "JsonlStore",
    "PrequentialEvaluator",
    "MetricMismatchError",
    # data — estado as-of + contrato do ciclo previsão→maturação
    "state_asof",
    "PredictionPoint",
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
    # contracts — ciclo econômico cross-domain
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
