"""Compatibility facade; new code should import explicit submodule APIs.

Importing the package does not load networking, persistence or measurement.
Legacy public names remain available through lazy attribute resolution.
"""

# ruff: noqa: F401

from importlib import import_module
from importlib.metadata import version
from typing import TYPE_CHECKING

if TYPE_CHECKING:
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
        DeflationNotEstimableError,
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

_EXPORTS = {
    "SCIENTIFIC_GOVERNANCE_SCHEMA_VERSION": (
        "predictor_core.contracts.scientific",
        "SCIENTIFIC_GOVERNANCE_SCHEMA_VERSION",
    ),
    "DataAcquisitionCharter": ("predictor_core.contracts.scientific", "DataAcquisitionCharter"),
    "DatasetFreeze": ("predictor_core.contracts.scientific", "DatasetFreeze"),
    "LatencySLA": ("predictor_core.contracts.scientific", "LatencySLA"),
    "ResourceBudget": ("predictor_core.contracts.scientific", "ResourceBudget"),
    "ScientificState": ("predictor_core.contracts.scientific", "ScientificState"),
    "ScientificTransitionError": (
        "predictor_core.contracts.scientific",
        "ScientificTransitionError",
    ),
    "TimestampSemantics": ("predictor_core.contracts.scientific", "TimestampSemantics"),
    "validate_scientific_transition": (
        "predictor_core.contracts.scientific",
        "validate_scientific_transition",
    ),
    "NOT_APPLICABLE": ("predictor_core.contracts.trial_v2", "NOT_APPLICABLE"),
    "TRIAL_SCHEMA_VERSION": ("predictor_core.contracts.trial_v2", "TRIAL_SCHEMA_VERSION"),
    "UNKNOWN": ("predictor_core.contracts.trial_v2", "UNKNOWN"),
    "TrialRegistryV2": ("predictor_core.contracts.trial_v2", "TrialRegistryV2"),
    "TrialSchemaError": ("predictor_core.contracts.trial_v2", "TrialSchemaError"),
    "current_code_version": ("predictor_core.contracts.trial_v2", "current_code_version"),
    "dataset_fingerprint": ("predictor_core.contracts.trial_v2", "dataset_fingerprint"),
    "migrate_legacy_registry": ("predictor_core.contracts.trial_v2", "migrate_legacy_registry"),
    "migrate_legacy_trial": ("predictor_core.contracts.trial_v2", "migrate_legacy_trial"),
    "require_trial_v2": ("predictor_core.contracts.trial_v2", "require_trial_v2"),
    "validate_trial_v2": ("predictor_core.contracts.trial_v2", "validate_trial_v2"),
    "COLLECTION_SCHEMA_VERSION": ("predictor_core.data.collection", "COLLECTION_SCHEMA_VERSION"),
    "CollectionArchive": ("predictor_core.data.collection", "CollectionArchive"),
    "CollectionTransitionError": ("predictor_core.data.collection", "CollectionTransitionError"),
    "LifecycleState": ("predictor_core.data.collection", "LifecycleState"),
    "ObservationEnvelope": ("predictor_core.data.collection", "ObservationEnvelope"),
    "ScientificPromotionError": ("predictor_core.data.collection", "ScientificPromotionError"),
    "aggregate_funnel": ("predictor_core.data.collection", "aggregate_funnel"),
    "PredictionPoint": ("predictor_core.data.contracts", "PredictionPoint"),
    "SourceQualityScorecard": ("predictor_core.data.source_quality", "SourceQualityScorecard"),
    "SourceQualityState": ("predictor_core.data.source_quality", "SourceQualityState"),
    "SourceQualityThresholds": ("predictor_core.data.source_quality", "SourceQualityThresholds"),
    "source_quality_scorecard": ("predictor_core.data.source_quality", "source_quality_scorecard"),
    "config_hash": ("predictor_core.kernel.infra", "config_hash"),
    "connect": ("predictor_core.kernel.infra", "connect"),
    "run_migrations": ("predictor_core.kernel.infra", "run_migrations"),
    "JsonlStore": ("predictor_core.kernel.jsonl_store", "JsonlStore"),
    "StaleModelError": ("predictor_core.kernel.meta", "StaleModelError"),
    "fingerprint": ("predictor_core.kernel.meta", "fingerprint"),
    "validate": ("predictor_core.kernel.meta", "validate"),
    "download_file": ("predictor_core.kernel.net", "download_file"),
    "sha256_file": ("predictor_core.kernel.net", "sha256_file"),
    "emit_event": ("predictor_core.kernel.obs", "emit_event"),
    "get_logger": ("predictor_core.kernel.obs", "get_logger"),
    "read_events": ("predictor_core.kernel.obs", "read_events"),
    "setup_logging": ("predictor_core.kernel.obs", "setup_logging"),
    "MissingCredentialsError": ("predictor_core.kernel.settings", "MissingCredentialsError"),
    "require_secrets": ("predictor_core.kernel.settings", "require_secrets"),
    "NaiveDatetimeError": ("predictor_core.kernel.timeindex", "NaiveDatetimeError"),
    "iso_z": ("predictor_core.kernel.timeindex", "iso_z"),
    "parse_iso": ("predictor_core.kernel.timeindex", "parse_iso"),
    "to_utc": ("predictor_core.kernel.timeindex", "to_utc"),
    "utcnow": ("predictor_core.kernel.timeindex", "utcnow"),
    "bootstrap_ci": ("predictor_core.measurement.bootstrap", "bootstrap_ci"),
    "brier": ("predictor_core.measurement.metrics", "brier"),
    "calibration_table": ("predictor_core.measurement.metrics", "calibration_table"),
    "diebold_mariano": ("predictor_core.measurement.metrics", "diebold_mariano"),
    "log_loss": ("predictor_core.measurement.metrics", "log_loss"),
    "rps": ("predictor_core.measurement.metrics", "rps"),
    "LookaheadError": ("predictor_core.measurement.replay", "LookaheadError"),
    "PastView": ("predictor_core.measurement.replay", "PastView"),
    "replay": ("predictor_core.measurement.replay", "replay"),
    "block_bootstrap_ci": ("predictor_core.measurement.stats", "block_bootstrap_ci"),
    "ci_mean": ("predictor_core.measurement.stats", "ci_mean"),
    "max_drawdown": ("predictor_core.measurement.stats", "max_drawdown"),
    "probabilistic_sharpe_ratio": (
        "predictor_core.measurement.stats",
        "probabilistic_sharpe_ratio",
    ),
    "sharpe": ("predictor_core.measurement.stats", "sharpe"),
    "sortino": ("predictor_core.measurement.stats", "sortino"),
    "spearman": ("predictor_core.measurement.stats", "spearman"),
    "spearman_block_ci": ("predictor_core.measurement.stats", "spearman_block_ci"),
    "DeflationNotEstimableError": (
        "predictor_core.measurement.trials",
        "DeflationNotEstimableError",
    ),
    "MetricMismatchError": ("predictor_core.measurement.trials", "MetricMismatchError"),
    "PowerAttestationMissingError": (
        "predictor_core.measurement.trials",
        "PowerAttestationMissingError",
    ),
    "TrialRegistry": ("predictor_core.measurement.trials", "TrialRegistry"),
    "attestation_path_for": ("predictor_core.measurement.trials", "attestation_path_for"),
    "deflated_sharpe_ratio": ("predictor_core.measurement.trials", "deflated_sharpe_ratio"),
    "load_trials": ("predictor_core.measurement.trials", "load_trials"),
    "register_trial": ("predictor_core.measurement.trials", "register_trial"),
    "validate_trials": ("predictor_core.measurement.trials", "validate_trials"),
    "PrequentialEvaluator": ("predictor_core.testing.prequential", "PrequentialEvaluator"),
}

__all__ = """__version__ connect run_migrations config_hash emit_event read_events setup_logging get_logger require_secrets MissingCredentialsError download_file sha256_file fingerprint validate StaleModelError sharpe sortino max_drawdown probabilistic_sharpe_ratio spearman spearman_block_ci bootstrap_ci block_bootstrap_ci ci_mean brier log_loss rps calibration_table diebold_mariano TrialRegistry register_trial load_trials validate_trials deflated_sharpe_ratio DeflationNotEstimableError attestation_path_for PowerAttestationMissingError replay PastView LookaheadError utcnow to_utc iso_z parse_iso NaiveDatetimeError JsonlStore PrequentialEvaluator MetricMismatchError PredictionPoint COLLECTION_SCHEMA_VERSION LifecycleState ObservationEnvelope CollectionArchive CollectionTransitionError ScientificPromotionError aggregate_funnel SCIENTIFIC_GOVERNANCE_SCHEMA_VERSION DataAcquisitionCharter DatasetFreeze TimestampSemantics LatencySLA ResourceBudget ScientificState ScientificTransitionError validate_scientific_transition SourceQualityScorecard SourceQualityState SourceQualityThresholds source_quality_scorecard TRIAL_SCHEMA_VERSION UNKNOWN NOT_APPLICABLE TrialSchemaError TrialRegistryV2 validate_trial_v2 require_trial_v2 migrate_legacy_trial migrate_legacy_registry dataset_fingerprint current_code_version""".split()  # pyright: ignore[reportUnsupportedDunderAll]  # noqa: E501


def __getattr__(name: str):
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module, attribute = _EXPORTS[name]
    value = getattr(import_module(module), attribute)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(__all__))
