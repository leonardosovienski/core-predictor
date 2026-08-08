from datetime import UTC, datetime

import pytest

from predictor_core.contracts.scientific import (
    DataAcquisitionCharter,
    DatasetFreeze,
    LatencySLA,
    ResourceBudget,
    ScientificState,
    ScientificTransitionError,
    TimestampSemantics,
    validate_scientific_transition,
)

T0 = datetime(2026, 8, 1, tzinfo=UTC)


def test_charter_requires_auditable_scope():
    charter = DataAcquisitionCharter(
        charter_id="crypto-derivatives-v1",
        source="kraken-futures",
        metrics=("funding", "open_interest"),
        assets=("BTC", "ETH"),
        cadence="5m",
        timestamp_semantics=TimestampSemantics("exchange", "exchange", "collector_clock"),
        latency_sla=LatencySLA(30, 60),
        resource_budget=ResourceBudget(500, 10),
        owner="research@example.test",
        revision_policy="append a new vintage; never overwrite",
        initial_scientific_state=ScientificState.COLLECTION_ONLY,
        collector_version="1.0.0",
        expected_schema_version="signals/2",
        retention_policy={"raw_days": 30, "aggregate": "permanent"},
        quality_thresholds={"minimum_coverage": 0.99},
        created_at=T0,
        rationale="Measure cross-exchange derivatives divergence.",
    )
    assert charter.to_dict()["created_at"].endswith("Z")


def test_freeze_is_deterministic_and_tamper_evident():
    freeze = DatasetFreeze(
        freeze_id="freeze-h6-v1",
        hypothesis_id="h6-cross-exchange-divergence",
        dataset_frozen_at=datetime(2026, 8, 2, tzinfo=UTC),
        period_start=datetime(2025, 1, 1, tzinfo=UTC),
        period_end=datetime(2026, 8, 1, tzinfo=UTC),
        oos_cutoff=datetime(2026, 1, 1, tzinfo=UTC),
        assets=("BTC", "ETH"),
        sources=("binance", "kraken"),
        metrics=("funding", "open_interest"),
        features=("funding_divergence", "oi_divergence"),
        feature_code_version="git:abc123",
        charter_hashes={"crypto-derivatives-v1": "c" * 64},
        hypothesis_registry_hash="d" * 64,
        collector_versions={"binance": "1", "kraken": "1"},
        schema_versions={"signals": "2"},
        partition_hashes={"2026-01": "a" * 64, "2026-02": "b" * 64},
        partition_roles={"2026-01": "IS", "2026-02": "OOS"},
        exclusion_policy={"maximum_staleness_seconds": 600},
    ).seal()
    assert freeze.verify()
    assert freeze.seal() == freeze
    object.__setattr__(freeze, "features", ("changed",))
    assert not freeze.verify()


def test_charter_rejects_missing_governance_fields():
    with pytest.raises(TypeError):
        DataAcquisitionCharter(  # type: ignore[call-arg]
            charter_id="incomplete",
            source="source",
            metrics=("funding",),
            assets=("BTC",),
            cadence="1h",
            created_at=T0,
            rationale="missing SLA and owner",
        )
    with pytest.raises(ValueError, match="COLLECTION_ONLY"):
        DataAcquisitionCharter(
            charter_id="invalid-state",
            source="source",
            metrics=("funding",),
            assets=("BTC",),
            cadence="1h",
            timestamp_semantics=TimestampSemantics("event", "public", "clock"),
            latency_sla=LatencySLA(10, 20),
            resource_budget=ResourceBudget(1, 1),
            owner="owner",
            revision_policy="append",
            initial_scientific_state=ScientificState.GO,
            collector_version="1",
            expected_schema_version="1",
            retention_policy={"days": 1},
            quality_thresholds={"minimum_coverage": 1},
            created_at=T0,
            rationale="invalid initial state",
        )


def test_scientific_transitions_cannot_skip_preregistration_or_freeze():
    validate_scientific_transition(
        ScientificState.COLLECTION_ONLY, ScientificState.HYPOTHESIS_REGISTERED
    )
    with pytest.raises(ScientificTransitionError):
        validate_scientific_transition(ScientificState.COLLECTION_ONLY, ScientificState.GO)
    with pytest.raises(ScientificTransitionError):
        validate_scientific_transition(
            ScientificState.HYPOTHESIS_REGISTERED, ScientificState.SHADOW
        )
