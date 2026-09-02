"""contracts.registry — caminho canônico da governança de experimentos (v1.3.0).

Fachada sobre `measurement/trials.py` (implementação física preservada).
Novo código importa daqui."""

from predictor_core.contracts.trial_v2 import (  # noqa: F401
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
from predictor_core.measurement.trials import (  # noqa: F401
    MetricMismatchError,
    PowerAttestationMissingError,
    TrialRegistry,
    attestation_path_for,
    deflated_sharpe_ratio,
    expected_max_sharpe,
    load_trials,
    register_trial,
    validate_trials,
)

__all__ = [
    "TrialRegistry",
    "register_trial",
    "load_trials",
    "validate_trials",
    "deflated_sharpe_ratio",
    "expected_max_sharpe",
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
]
