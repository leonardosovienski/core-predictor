"""Public facade for the small, shared predictor scientific kernel."""

# ruff: noqa: F401

from importlib.metadata import version

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
from predictor_core.contracts.trial_v2 import (
    NOT_APPLICABLE,
    TRIAL_SCHEMA_VERSION,
    UNKNOWN,
    TrialRegistryV2,
    TrialSchemaError,
    current_code_version,
    dataset_fingerprint,
    migrate_legacy_registry,
    migrate_legacy_trial,
    require_trial_v2,
    validate_trial_v2,
)
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
from predictor_core.kernel.settings import MissingCredentialsError, require_secrets
from predictor_core.kernel.timeindex import NaiveDatetimeError, iso_z, parse_iso, to_utc, utcnow
from predictor_core.measurement.bootstrap import bootstrap_ci
from predictor_core.measurement.metrics import (
    brier,
    calibration_table,
    diebold_mariano,
    log_loss,
    rps,
)
from predictor_core.measurement.replay import LookaheadError, PastView, replay
from predictor_core.measurement.stats import (
    block_bootstrap_ci,
    ci_mean,
    max_drawdown,
    probabilistic_sharpe_ratio,
    sharpe,
    sortino,
    spearman,
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

__version__ = version("predictor-core")

__all__ = """__version__ connect run_migrations config_hash emit_event read_events setup_logging get_logger require_secrets MissingCredentialsError download_file sha256_file fingerprint validate StaleModelError sharpe sortino max_drawdown probabilistic_sharpe_ratio spearman spearman_block_ci bootstrap_ci block_bootstrap_ci ci_mean brier log_loss rps calibration_table diebold_mariano TrialRegistry register_trial load_trials validate_trials deflated_sharpe_ratio attestation_path_for PowerAttestationMissingError replay PastView LookaheadError utcnow to_utc iso_z parse_iso NaiveDatetimeError JsonlStore PrequentialEvaluator MetricMismatchError PredictionPoint COLLECTION_SCHEMA_VERSION LifecycleState ObservationEnvelope CollectionArchive CollectionTransitionError ScientificPromotionError aggregate_funnel SCIENTIFIC_GOVERNANCE_SCHEMA_VERSION DataAcquisitionCharter DatasetFreeze TimestampSemantics LatencySLA ResourceBudget ScientificState ScientificTransitionError validate_scientific_transition SourceQualityScorecard SourceQualityState SourceQualityThresholds source_quality_scorecard TRIAL_SCHEMA_VERSION UNKNOWN NOT_APPLICABLE TrialSchemaError TrialRegistryV2 validate_trial_v2 require_trial_v2 migrate_legacy_trial migrate_legacy_registry dataset_fingerprint current_code_version""".split()  # pyright: ignore[reportUnsupportedDunderAll]  # noqa: E501
