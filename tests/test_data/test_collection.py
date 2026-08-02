from datetime import UTC, datetime, timedelta

import pytest

from predictor_core.contracts.collection import (
    CollectionArchive,
    CollectionTransitionError,
    LifecycleState,
    ObservationEnvelope,
    ScientificPromotionError,
    aggregate_funnel,
)

T0 = datetime(2026, 7, 23, 12, tzinfo=UTC)
HASH = "a" * 64


def envelope(**changes):
    row = dict(
        collection_run_id="run-20260723-a",
        project="lol-predictor",
        domain="lol",
        canonical_event_id="lol:series:123",
        observed_at=T0,
        scheduled_at=T0 + timedelta(hours=2),
        source="official",
        source_record_id="123",
        provenance_hash=HASH,
        source_snapshot_hash="b" * 64,
        code_commit="abc123",
        core_version="1.3.3-ga-20260723",
        participants={"a": "A", "b": "B"},
        competition={"id": "lck", "name": "LCK"},
        created_at=T0,
        updated_at=T0,
    )
    row.update(changes)
    return ObservationEnvelope(**row)


def test_complete_flow_and_append_only_history(tmp_path):
    archive = CollectionArchive(tmp_path / "collection.jsonl")
    current = archive.append(envelope())
    for i, state in enumerate(
        (
            LifecycleState.VALIDATED,
            LifecycleState.SNAPSHOT_RECORDED,
            LifecycleState.EVENT_STARTED,
            LifecycleState.OFFICIAL_RESULT_FOUND,
            LifecycleState.COMPLETE,
        ),
        start=1,
    ):
        result = (
            {"winner": "A"}
            if state in {LifecycleState.OFFICIAL_RESULT_FOUND, LifecycleState.COMPLETE}
            else None
        )
        current = current.transition(state, at=T0 + timedelta(minutes=i), official_result=result)
        archive.append(current)
    history = archive.history("run-20260723-a", "lol:series:123")
    assert [item.lifecycle_state for item in history] == [
        LifecycleState.DISCOVERED,
        LifecycleState.VALIDATED,
        LifecycleState.SNAPSHOT_RECORDED,
        LifecycleState.EVENT_STARTED,
        LifecycleState.OFFICIAL_RESULT_FOUND,
        LifecycleState.COMPLETE,
    ]
    assert all(item.created_at == T0 for item in history)


def test_duplicate_is_idempotent_but_changed_same_state_is_rejected(tmp_path):
    archive = CollectionArchive(tmp_path / "collection.jsonl")
    first = archive.append(envelope())
    assert archive.append(first) == first
    with pytest.raises(CollectionTransitionError):
        archive.append(envelope(updated_at=T0 + timedelta(minutes=1)))


def test_retry_missing_result_stale_ambiguous_and_invalid_transition():
    first = envelope()
    assert first.transition(LifecycleState.DISCOVERED) is first
    with pytest.raises(ValueError, match="exige official_result"):
        first.transition(LifecycleState.VALIDATED, at=T0 + timedelta(minutes=1)).transition(
            LifecycleState.SNAPSHOT_RECORDED, at=T0 + timedelta(minutes=2)
        ).transition(LifecycleState.EVENT_STARTED, at=T0 + timedelta(minutes=3)).transition(
            LifecycleState.OFFICIAL_RESULT_FOUND, at=T0 + timedelta(minutes=4)
        ).transition(LifecycleState.COMPLETE, at=T0 + timedelta(minutes=5))
    stale = first.transition(
        LifecycleState.STALE, at=T0 + timedelta(minutes=1), rejection_reason="snapshot venceu"
    )
    with pytest.raises(CollectionTransitionError):
        stale.transition(LifecycleState.VALIDATED, at=T0 + timedelta(minutes=2))
    with pytest.raises(ValueError, match="rejection_reason"):
        envelope(lifecycle_state=LifecycleState.IDENTITY_AMBIGUOUS)
    with pytest.raises(CollectionTransitionError):
        first.transition(LifecycleState.EVENT_STARTED, at=T0 + timedelta(minutes=1))


def test_collection_cannot_be_scientific_or_reclassified_as_new(tmp_path):
    with pytest.raises(ValueError, match="científico"):
        envelope(lifecycle_state="GO")
    with pytest.raises(ValueError, match="não pode ser trial_id"):
        envelope(collection_run_id="trial-h4")
    with pytest.raises(ScientificPromotionError):
        envelope().as_scientific_trial()
    archive = CollectionArchive(tmp_path / "collection.jsonl")
    first = archive.append(envelope())
    changed = first.transition(LifecycleState.VALIDATED, at=T0 + timedelta(minutes=1))
    object.__setattr__(changed, "created_at", T0 + timedelta(minutes=1))
    with pytest.raises(CollectionTransitionError, match="reclassificada"):
        archive.append(changed)


def test_funnel_filters_project_run_and_window():
    done = (
        envelope()
        .transition(LifecycleState.VALIDATED, at=T0 + timedelta(minutes=1))
        .transition(LifecycleState.SNAPSHOT_RECORDED, at=T0 + timedelta(minutes=2))
        .transition(LifecycleState.EVENT_STARTED, at=T0 + timedelta(minutes=3))
        .transition(
            LifecycleState.OFFICIAL_RESULT_FOUND,
            at=T0 + timedelta(minutes=4),
            official_result={"winner": "A"},
        )
        .transition(
            LifecycleState.COMPLETE, at=T0 + timedelta(minutes=5), official_result={"winner": "A"}
        )
    )
    other = envelope(canonical_event_id="lol:series:124", collection_run_id="run-20260723-b")
    report = aggregate_funnel(
        [envelope(), done, other],
        project="lol-predictor",
        collection_run_id="run-20260723-a",
        start_at=T0 - timedelta(seconds=1),
        end_at=T0 + timedelta(days=1),
    )
    assert report["events"] == 1 and report["complete"] == 1 and report["collection_only"] is True
