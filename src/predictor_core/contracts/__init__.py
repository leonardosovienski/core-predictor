"""Compatibility facade; new code should import explicit submodule APIs.

Importing the package does not load networking, persistence or measurement.
Legacy public names remain available through lazy attribute resolution.
"""

from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from predictor_core.contracts.collection import (  # noqa: F401
        COLLECTION_SCHEMA_VERSION,
        CollectionArchive,
        CollectionTransitionError,
        LifecycleState,
        ObservationEnvelope,
        ScientificPromotionError,
        aggregate_funnel,
    )
    from predictor_core.contracts.points import (  # noqa: F401
        DataUnavailableError,
        MarketDataPoint,
        PredictionPoint,
        SignalPoint,
    )
    from predictor_core.contracts.registry import (  # noqa: F401
        NOT_APPLICABLE,
        TRIAL_SCHEMA_VERSION,
        UNKNOWN,
        DeflationNotEstimableError,
        MetricMismatchError,
        PowerAttestationMissingError,
        TrialRegistry,
        TrialRegistryV2,
        TrialSchemaError,
        attestation_path_for,
        current_code_version,
        dataset_fingerprint,
        deflated_sharpe_ratio,
        load_trials,
        migrate_legacy_registry,
        migrate_legacy_trial,
        register_trial,
        require_trial_v2,
        validate_trial_v2,
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
    from predictor_core.kernel.jsonable import to_jsonable


_EXPORTS = {
    "COLLECTION_SCHEMA_VERSION": (
        "predictor_core.contracts.collection",
        "COLLECTION_SCHEMA_VERSION",
    ),
    "CollectionArchive": ("predictor_core.contracts.collection", "CollectionArchive"),
    "CollectionTransitionError": (
        "predictor_core.contracts.collection",
        "CollectionTransitionError",
    ),
    "LifecycleState": ("predictor_core.contracts.collection", "LifecycleState"),
    "ObservationEnvelope": ("predictor_core.contracts.collection", "ObservationEnvelope"),
    "ScientificPromotionError": ("predictor_core.contracts.collection", "ScientificPromotionError"),
    "aggregate_funnel": ("predictor_core.contracts.collection", "aggregate_funnel"),
    "DataUnavailableError": ("predictor_core.contracts.points", "DataUnavailableError"),
    "MarketDataPoint": ("predictor_core.contracts.points", "MarketDataPoint"),
    "PredictionPoint": ("predictor_core.contracts.points", "PredictionPoint"),
    "SignalPoint": ("predictor_core.contracts.points", "SignalPoint"),
    "NOT_APPLICABLE": ("predictor_core.contracts.registry", "NOT_APPLICABLE"),
    "TRIAL_SCHEMA_VERSION": ("predictor_core.contracts.registry", "TRIAL_SCHEMA_VERSION"),
    "UNKNOWN": ("predictor_core.contracts.registry", "UNKNOWN"),
    "DeflationNotEstimableError": (
        "predictor_core.contracts.registry",
        "DeflationNotEstimableError",
    ),
    "MetricMismatchError": ("predictor_core.contracts.registry", "MetricMismatchError"),
    "PowerAttestationMissingError": (
        "predictor_core.contracts.registry",
        "PowerAttestationMissingError",
    ),
    "TrialRegistry": ("predictor_core.contracts.registry", "TrialRegistry"),
    "TrialRegistryV2": ("predictor_core.contracts.registry", "TrialRegistryV2"),
    "TrialSchemaError": ("predictor_core.contracts.registry", "TrialSchemaError"),
    "attestation_path_for": ("predictor_core.contracts.registry", "attestation_path_for"),
    "current_code_version": ("predictor_core.contracts.registry", "current_code_version"),
    "dataset_fingerprint": ("predictor_core.contracts.registry", "dataset_fingerprint"),
    "deflated_sharpe_ratio": ("predictor_core.contracts.registry", "deflated_sharpe_ratio"),
    "load_trials": ("predictor_core.contracts.registry", "load_trials"),
    "migrate_legacy_registry": ("predictor_core.contracts.registry", "migrate_legacy_registry"),
    "migrate_legacy_trial": ("predictor_core.contracts.registry", "migrate_legacy_trial"),
    "register_trial": ("predictor_core.contracts.registry", "register_trial"),
    "require_trial_v2": ("predictor_core.contracts.registry", "require_trial_v2"),
    "validate_trial_v2": ("predictor_core.contracts.registry", "validate_trial_v2"),
    "validate_trials": ("predictor_core.contracts.registry", "validate_trials"),
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
    "SourceQualityScorecard": ("predictor_core.data.source_quality", "SourceQualityScorecard"),
    "SourceQualityState": ("predictor_core.data.source_quality", "SourceQualityState"),
    "SourceQualityThresholds": ("predictor_core.data.source_quality", "SourceQualityThresholds"),
    "source_quality_scorecard": ("predictor_core.data.source_quality", "source_quality_scorecard"),
    "to_jsonable": ("predictor_core.kernel.jsonable", "to_jsonable"),
}

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
    "DeflationNotEstimableError",
    "attestation_path_for",
    "PowerAttestationMissingError",
    "MetricMismatchError",
    "TRIAL_SCHEMA_VERSION",
    "UNKNOWN",
    "NOT_APPLICABLE",
    "TrialSchemaError",
    "TrialRegistryV2",
    "validate_trial_v2",
    "require_trial_v2",
    "migrate_legacy_trial",
    "migrate_legacy_registry",
    "dataset_fingerprint",
    "current_code_version",
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
]


def __getattr__(name: str):
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module, attribute = _EXPORTS[name]
    value = getattr(import_module(module), attribute)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(__all__))
