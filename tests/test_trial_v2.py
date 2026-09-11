import json
import tomllib
from pathlib import Path

import pytest

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


def complete_trial(**changes):
    row = {
        "schema_version": TRIAL_SCHEMA_VERSION,
        "experiment_id": "exp-000b",
        "hypothesis_id": "h-1",
        "hypothesis_family": "xg_incrementality",
        "trial_id": "trial-d",
        "registered_at": "2026-09-01T10:00:00Z",
        "executed_at": "2026-09-01T11:00:00Z",
        "seed": 42,
        "forecast_horizon": "7d",
        "data_cutoff": "2026-08-31T23:59:59Z",
        "label_start": "2026-09-01T00:00:00Z",
        "label_end": "2026-09-08T00:00:00Z",
        "dataset_hash": "sha256:" + "a" * 64,
        "dataset_version": "matches-v4",
        "feature_version": "features-v7",
        "model_version": "model-v2",
        "code_version": "package:3.1.0;git:" + "b" * 40,
        "params": {"alpha": 0.1},
        "selection_path": {
            "family": "xg_incrementality",
            "candidate_set": ["A", "B", "C", "D"],
            "selection_metric": "validation_rps",
            "selected_candidate": "D",
            "thresholds": {"max_rps": 0.2},
            "preceding_trials": ["trial-a", "trial-b", "trial-c"],
        },
        "n_trials_family": 4,
        "n_trials_domain": "known_trials >= 29",
        "n_trials_ecosystem": "known_trials >= 51",
        "metric": "rps",
        "result": {"rps": 0.184},
        "status": "COMPLETE",
        "notes": "prospective",
    }
    row.update(changes)
    return row


def test_complete_prospective_trial_validates():
    assert validate_trial_v2(complete_trial()) == []


@pytest.mark.parametrize("field", ["seed", "dataset_hash", "hypothesis_family"])
def test_prospective_writer_rejects_silently_incomplete_trial(tmp_path, field):
    row = complete_trial()
    del row[field]
    with pytest.raises(TrialSchemaError, match="missing required fields"):
        TrialRegistryV2(tmp_path / "trials-v2.json").register(row)
    assert not (tmp_path / "trials-v2.json").exists()


def test_unknown_is_legacy_only_and_not_applicable_is_explicit():
    assert any(
        "UNKNOWN is reserved" in error for error in validate_trial_v2(complete_trial(seed=UNKNOWN))
    )
    assert validate_trial_v2(complete_trial(seed=NOT_APPLICABLE)) == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("executed_at", NOT_APPLICABLE),
        ("selection_path", NOT_APPLICABLE),
        ("metric", NOT_APPLICABLE),
    ],
)
def test_not_applicable_cannot_hide_universal_prospective_provenance(field, value):
    assert validate_trial_v2(complete_trial(**{field: value}))


def test_selection_path_and_relevant_selection_space_are_required():
    row = complete_trial(selection_path={"family": "x"}, n_trials_family=0)
    errors = validate_trial_v2(row)
    assert any("selection_path" in error for error in errors)
    assert any("n_trials_family" in error for error in errors)


def test_registry_rejects_duplicate_trial_identity(tmp_path):
    registry = TrialRegistryV2(tmp_path / "trials-v2.json")
    registry.register(complete_trial())
    with pytest.raises(TrialSchemaError, match="already registered"):
        registry.register(complete_trial())


def test_legacy_trial_migration_preserves_facts_and_marks_unknown():
    legacy = {
        "name": "H4_DIXON",
        "registered_at": "2026-07-01T00:00:00Z",
        "params": {"rho": -0.1},
        "sharpe": 0.2,
        "metric": "rps",
        "notes": "recorded",
    }
    migrated = migrate_legacy_trial(legacy)
    assert migrated["trial_id"] == "H4_DIXON"
    assert migrated["params"] == {"rho": -0.1}
    assert migrated["result"] == {"sharpe": 0.2}
    assert migrated["dataset_hash"] == UNKNOWN
    assert migrated["code_version"] == UNKNOWN
    assert validate_trial_v2(migrated, legacy_mode=True) == []


def test_legacy_missing_fields_remain_unknown():
    migrated = migrate_legacy_trial({"name": "old"})
    assert migrated["registered_at"] == UNKNOWN
    assert migrated["params"] == UNKNOWN
    assert migrated["notes"] == UNKNOWN


def test_invalid_legacy_value_is_not_silently_repaired():
    with pytest.raises(TrialSchemaError, match="registered_at"):
        migrate_legacy_trial({"name": "old", "registered_at": "yesterday"})


def test_registry_migration_is_non_destructive_and_idempotent(tmp_path):
    source = tmp_path / "legacy.json"
    destination = tmp_path / "v2.json"
    original = '[{"name":"old","params":{"x":1}}]\n'
    source.write_text(original, encoding="utf-8")
    first = migrate_legacy_registry(source, destination)
    before = destination.read_bytes()
    second = migrate_legacy_registry(source, destination)
    assert first == second
    assert destination.read_bytes() == before
    assert source.read_text(encoding="utf-8") == original
    assert json.loads(destination.read_text(encoding="utf-8"))[0]["dataset_hash"] == UNKNOWN


def test_migration_refuses_to_overwrite_original(tmp_path):
    source = tmp_path / "legacy.json"
    source.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="destination must differ"):
        migrate_legacy_registry(source, source)


def test_dataset_fingerprint_contract_covers_rows_fields_and_order():
    rows = [{"id": 1, "value": 2, "ignored": 9}, {"id": 2, "value": 3, "ignored": 8}]
    digest = dataset_fingerprint(rows, fields=["id", "value"])
    assert digest == dataset_fingerprint(rows, fields=["id", "value"])
    assert digest != dataset_fingerprint(list(reversed(rows)), fields=["id", "value"])
    assert digest == dataset_fingerprint(
        list(reversed(rows)), fields=["id", "value"], order_matters=False
    )


def test_code_version_reports_package_and_real_git_sha():
    value = current_code_version()
    project = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text())
    assert value.startswith(f"package:{project['project']['version']};git:")
    assert "git:" + "0" * 40 not in value


def test_require_trial_rejects_non_json_result():
    with pytest.raises(TrialSchemaError, match="result"):
        require_trial_v2(complete_trial(result={"bad": float("nan")}))
