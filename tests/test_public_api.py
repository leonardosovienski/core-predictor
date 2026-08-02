import importlib

import predictor_core

EXPECTED_PUBLIC_API = frozenset(
    """__version__ connect run_migrations config_hash emit_event read_events setup_logging
    get_logger require_secrets MissingCredentialsError download_file sha256_file fingerprint
    validate StaleModelError sharpe sortino max_drawdown probabilistic_sharpe_ratio spearman
    spearman_block_ci bootstrap_ci block_bootstrap_ci ci_mean brier log_loss rps
    calibration_table diebold_mariano TrialRegistry register_trial load_trials validate_trials
    deflated_sharpe_ratio attestation_path_for PowerAttestationMissingError null_distribution
    tail_probability percentile_of random_portfolio_sequence replay PastView LookaheadError
    Posting Transaction Ledger UnbalancedTransactionError plackett_luce_prob
    fit_plackett_luce rank_probabilities Entity expected_score update_pair RatingBook
    check_property floats integers lists_of PropertyFailure PlattCalibrator shin_devig utcnow
    to_utc iso_z parse_iso NaiveDatetimeError JsonlStore PrequentialEvaluator
    MetricMismatchError state_asof PredictionPoint COLLECTION_SCHEMA_VERSION LifecycleState
    ObservationEnvelope CollectionArchive CollectionTransitionError ScientificPromotionError
    aggregate_funnel""".split()
)


def test_public_facade_exact_snapshot():
    assert frozenset(predictor_core.__all__) == EXPECTED_PUBLIC_API
    assert all(hasattr(predictor_core, name) for name in EXPECTED_PUBLIC_API)


def test_temporary_flat_package_shims_import():
    for name in ("infra", "net", "obs", "replay", "settings", "stats"):
        module = importlib.import_module(f"predictor_core.{name}")
        assert module.__name__ == f"predictor_core.{name}"
