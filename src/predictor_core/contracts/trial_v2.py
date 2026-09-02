"""Prospective, auditable trial provenance contract.

The legacy registry remains available for existing consumers.  This module is the
strict boundary for new trials and the non-destructive bridge for historical rows.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections.abc import Iterable, Mapping, Sequence
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

TRIAL_SCHEMA_VERSION = "trial-registry/2.0.0"
UNKNOWN = "UNKNOWN"
NOT_APPLICABLE = "NOT_APPLICABLE"

TRIAL_V2_FIELDS = (
    "schema_version",
    "experiment_id",
    "hypothesis_id",
    "hypothesis_family",
    "trial_id",
    "registered_at",
    "executed_at",
    "seed",
    "forecast_horizon",
    "data_cutoff",
    "label_start",
    "label_end",
    "dataset_hash",
    "dataset_version",
    "feature_version",
    "model_version",
    "code_version",
    "params",
    "selection_path",
    "n_trials_family",
    "n_trials_domain",
    "n_trials_ecosystem",
    "metric",
    "result",
    "status",
    "notes",
)

_IDENTITY_FIELDS = ("experiment_id", "hypothesis_id", "hypothesis_family", "trial_id")
_REQUIRED_TIME_FIELDS = ("registered_at", "executed_at", "data_cutoff")
_OPTIONAL_TIME_FIELDS = ("label_start", "label_end")
_COUNT_FIELDS = ("n_trials_family", "n_trials_domain", "n_trials_ecosystem")
_SELECTION_FIELDS = ("family", "candidate_set", "selection_metric", "selected_candidate")
_HASH_RE = re.compile(r"^(?:sha256:)?[0-9a-f]{64}$")
_LOWER_BOUND_RE = re.compile(r"^known_trials\s*>=\s*[1-9][0-9]*$")


class TrialSchemaError(ValueError):
    """A trial cannot cross the requested registry boundary."""


def _utc_z(value: object) -> bool:
    if not isinstance(value, str) or not value.endswith("Z"):
        return False
    try:
        from datetime import datetime

        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return False
    return parsed.utcoffset() is not None


def _json_native(value: object) -> bool:
    try:
        json.dumps(value, allow_nan=False)
    except (TypeError, ValueError):
        return False
    return True


def validate_trial_v2(trial: Mapping[str, Any], *, legacy_mode: bool = False) -> list[str]:
    """Return violations for one V2 row.

    ``legacy_mode`` permits ``UNKNOWN`` because historical facts must not be
    invented.  Prospective rows reject ``UNKNOWN`` and require real dataset and
    code identities. ``NOT_APPLICABLE`` remains explicit in either mode.
    """
    errors: list[str] = []
    if not isinstance(trial, Mapping):
        return ["trial must be a JSON object"]
    missing = [field for field in TRIAL_V2_FIELDS if field not in trial]
    extra = sorted(set(trial) - set(TRIAL_V2_FIELDS))
    if missing:
        errors.append(f"missing required fields: {missing}")
    if extra:
        errors.append(f"unknown fields: {extra}")
    if missing:
        return errors
    if trial["schema_version"] != TRIAL_SCHEMA_VERSION:
        errors.append(f"schema_version must be {TRIAL_SCHEMA_VERSION!r}")
    if not legacy_mode and any(value == UNKNOWN for value in trial.values()):
        errors.append("UNKNOWN is reserved for legacy migration")
    for field in _IDENTITY_FIELDS:
        value = trial[field]
        if value == UNKNOWN and legacy_mode:
            continue
        if not isinstance(value, str) or not value or value == NOT_APPLICABLE:
            errors.append(f"{field} must be a non-empty identity")
    for field in _REQUIRED_TIME_FIELDS:
        value = trial[field]
        if value == UNKNOWN and legacy_mode:
            continue
        if not _utc_z(value):
            errors.append(f"{field} must be ISO-8601 UTC ending in Z")
    for field in _OPTIONAL_TIME_FIELDS:
        value = trial[field]
        if value in ({UNKNOWN, NOT_APPLICABLE} if legacy_mode else {NOT_APPLICABLE}):
            continue
        if not _utc_z(value):
            errors.append(f"{field} must be ISO-8601 UTC ending in Z or an explicit sentinel")
    seed = trial["seed"]
    allowed_seed_sentinels = {NOT_APPLICABLE} | ({UNKNOWN} if legacy_mode else set())
    if seed not in allowed_seed_sentinels and (isinstance(seed, bool) or not isinstance(seed, int)):
        errors.append("seed must be an integer or an explicit sentinel")
    if not (trial["params"] == UNKNOWN and legacy_mode) and (
        not isinstance(trial["params"], Mapping) or not trial["params"]
    ):
        errors.append("params must be a non-empty object")
    selection = trial["selection_path"]
    if selection == UNKNOWN and legacy_mode:
        pass
    elif not isinstance(selection, Mapping) or any(
        field not in selection for field in _SELECTION_FIELDS
    ):
        errors.append(f"selection_path must contain {list(_SELECTION_FIELDS)}")
    for field in _COUNT_FIELDS:
        count = trial[field]
        allowed = count == UNKNOWN and legacy_mode
        if not allowed and not (
            isinstance(count, int)
            and not isinstance(count, bool)
            and count >= 1
            or isinstance(count, str)
            and _LOWER_BOUND_RE.fullmatch(count)
        ):
            errors.append(f"{field} must be a positive integer or 'known_trials >= N'")
    dataset_hash = trial["dataset_hash"]
    if not (dataset_hash == UNKNOWN and legacy_mode) and not (
        isinstance(dataset_hash, str) and _HASH_RE.fullmatch(dataset_hash)
    ):
        errors.append("dataset_hash must be a SHA-256 fingerprint of the data actually used")
    code_version = trial["code_version"]
    if not (code_version == UNKNOWN and legacy_mode) and (
        not isinstance(code_version, str) or not code_version or code_version == NOT_APPLICABLE
    ):
        errors.append("code_version must identify real executing code")
    for field in ("forecast_horizon", "dataset_version", "feature_version", "model_version"):
        value = trial[field]
        if value == UNKNOWN and legacy_mode:
            continue
        if not isinstance(value, str) or not value:
            errors.append(f"{field} must be a non-empty string or explicit sentinel")
    for field in ("metric", "status", "notes"):
        value = trial[field]
        if value == UNKNOWN and legacy_mode:
            continue
        if not isinstance(value, str) or (field != "notes" and not value):
            errors.append(f"{field} must be a {'non-empty ' if field != 'notes' else ''}string")
        elif field == "metric" and value == NOT_APPLICABLE:
            errors.append("metric is always applicable to a prospective trial")
    if not _json_native(trial["result"]):
        errors.append("result must contain finite, JSON-native values")
    if not _json_native(dict(trial)):
        errors.append("trial must contain only finite, JSON-native values")
    return errors


def require_trial_v2(trial: Mapping[str, Any], *, legacy_mode: bool = False) -> dict[str, Any]:
    errors = validate_trial_v2(trial, legacy_mode=legacy_mode)
    if errors:
        raise TrialSchemaError("; ".join(errors))
    return dict(trial)


def dataset_fingerprint(
    rows: Iterable[Mapping[str, Any]], *, fields: Sequence[str], order_matters: bool = True
) -> str:
    """Hash the selected fields of the actual rows using canonical UTF-8 JSON.

    Field order is the supplied ``fields`` order. Mapping keys are sorted, no
    whitespace is emitted and NaN/Infinity are rejected. If row order is declared
    irrelevant, canonical row encodings are sorted before hashing.
    """
    if not fields or len(set(fields)) != len(fields):
        raise ValueError("fields must be a non-empty sequence of unique names")
    encoded: list[str] = []
    for index, row in enumerate(rows):
        absent = [field for field in fields if field not in row]
        if absent:
            raise ValueError(f"row {index} is missing fingerprint fields: {absent}")
        selected = {field: row[field] for field in fields}
        encoded.append(json.dumps(selected, sort_keys=True, separators=(",", ":"), allow_nan=False))
    if not order_matters:
        encoded.sort()
    payload = ("\n".join(encoded) + "\n").encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def current_code_version(repo: Path | str | None = None) -> str:
    """Return a truthful package version plus Git SHA and dirty state when available."""
    try:
        package = version("predictor-core")
    except PackageNotFoundError:
        package = "uninstalled"
    cwd = Path(repo) if repo is not None else Path.cwd()
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=cwd, check=True, capture_output=True, text=True
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=cwd,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
    except (OSError, subprocess.CalledProcessError):
        return f"package:{package}"
    return f"package:{package};git:{sha}{';dirty' if dirty else ''}"


def migrate_legacy_trial(trial: Mapping[str, Any]) -> dict[str, Any]:
    """Copy recorded legacy facts into V2; never infer missing history."""
    if not isinstance(trial, Mapping):
        raise TrialSchemaError("legacy trial must be a JSON object")
    name = trial.get("name", UNKNOWN)
    migrated: dict[str, Any] = {field: UNKNOWN for field in TRIAL_V2_FIELDS}
    migrated.update(
        {
            "schema_version": TRIAL_SCHEMA_VERSION,
            "trial_id": name if isinstance(name, str) and name else UNKNOWN,
            "registered_at": trial.get("registered_at", UNKNOWN),
            "params": trial.get("params", UNKNOWN),
            "metric": trial.get("metric", UNKNOWN),
            "result": {"sharpe": trial["sharpe"]} if "sharpe" in trial else UNKNOWN,
            "status": trial.get("status", UNKNOWN),
            "notes": trial.get("notes", UNKNOWN),
        }
    )
    return require_trial_v2(migrated, legacy_mode=True)


def migrate_legacy_registry(source: Path | str, destination: Path | str) -> list[dict[str, Any]]:
    """Write a validated V2 copy without changing or overwriting the source."""
    src, dst = Path(source), Path(destination)
    if src.resolve() == dst.resolve():
        raise ValueError("destination must differ from the legacy source")
    parsed = json.loads(src.read_text(encoding="utf-8"))
    if not isinstance(parsed, list):
        raise TrialSchemaError("legacy registry must contain a JSON list")
    migrated = [migrate_legacy_trial(row) for row in parsed]
    serialized = json.dumps(migrated, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if dst.exists() and dst.read_text(encoding="utf-8") == serialized:
        return migrated
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(dst.suffix + ".tmp")
    tmp.write_text(serialized, encoding="utf-8")
    tmp.replace(dst)
    return migrated


class TrialRegistryV2:
    """Strict, append-only-by-identity writer for prospective V2 trials."""

    def __init__(self, path: Path | str):
        self.path = Path(path)

    def load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        parsed = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(parsed, list):
            raise TrialSchemaError("V2 registry must contain a JSON list")
        return [require_trial_v2(row) for row in parsed]

    def register(self, trial: Mapping[str, Any]) -> list[dict[str, Any]]:
        row = require_trial_v2(trial)
        rows = self.load()
        if any(existing["trial_id"] == row["trial_id"] for existing in rows):
            raise TrialSchemaError(f"trial_id already registered: {row['trial_id']!r}")
        rows.append(row)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(rows, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(serialized, encoding="utf-8")
        tmp.replace(self.path)
        return rows
