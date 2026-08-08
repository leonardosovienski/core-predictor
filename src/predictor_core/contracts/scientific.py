"""Scientific governance contracts shared by Predictor domains."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, replace
from datetime import datetime
from enum import StrEnum
from typing import Any

from predictor_core.kernel.timeindex import iso_z, to_utc

SCIENTIFIC_GOVERNANCE_SCHEMA_VERSION = "scientific-governance/1"


class ScientificState(StrEnum):
    COLLECTION_ONLY = "COLLECTION_ONLY"
    HYPOTHESIS_REGISTERED = "HYPOTHESIS_REGISTERED"
    DATASET_FROZEN = "DATASET_FROZEN"
    PENDING_SAMPLE = "PENDING_SAMPLE"
    SHADOW = "SHADOW"
    GO = "GO"
    NO_GO = "NO_GO"
    CLOSED_BY_HUMAN_DECISION = "CLOSED_BY_HUMAN_DECISION"


_TRANSITIONS = {
    ScientificState.COLLECTION_ONLY: {ScientificState.HYPOTHESIS_REGISTERED},
    ScientificState.HYPOTHESIS_REGISTERED: {ScientificState.DATASET_FROZEN},
    ScientificState.DATASET_FROZEN: {ScientificState.PENDING_SAMPLE, ScientificState.SHADOW},
    ScientificState.PENDING_SAMPLE: {ScientificState.SHADOW},
    ScientificState.SHADOW: {ScientificState.GO, ScientificState.NO_GO},
    ScientificState.GO: {ScientificState.CLOSED_BY_HUMAN_DECISION},
    ScientificState.NO_GO: {ScientificState.CLOSED_BY_HUMAN_DECISION},
    ScientificState.CLOSED_BY_HUMAN_DECISION: set(),
}


class ScientificTransitionError(ValueError):
    """Raised when scientific evidence is promoted out of order."""


def validate_scientific_transition(current: ScientificState, target: ScientificState) -> None:
    if target == current:
        return
    if target not in _TRANSITIONS[current]:
        raise ScientificTransitionError(f"invalid scientific transition: {current} -> {target}")


def _required_text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is required")
    return value


def _aware(value: datetime, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be a timezone-aware datetime")
    try:
        return to_utc(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be timezone-aware") from exc


def _jsonable(value: Any, field: str) -> None:
    try:
        json.dumps(value, allow_nan=False, sort_keys=True)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be canonical JSON") from exc


def _sha256(value: str, field: str) -> str:
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value.lower()):
        raise ValueError(f"{field} must be a hexadecimal SHA-256")
    return value.lower()


@dataclass(frozen=True)
class TimestampSemantics:
    event_at_source: str
    published_at_source: str
    ingested_at_source: str

    def __post_init__(self) -> None:
        for field in ("event_at_source", "published_at_source", "ingested_at_source"):
            _required_text(getattr(self, field), field)


@dataclass(frozen=True)
class LatencySLA:
    median_seconds: float
    p99_seconds: float

    def __post_init__(self) -> None:
        if self.median_seconds < 0 or self.p99_seconds < self.median_seconds:
            raise ValueError("latency SLA requires 0 <= median_seconds <= p99_seconds")


@dataclass(frozen=True)
class ResourceBudget:
    traffic_mb_month: float
    storage_gb_month: float

    def __post_init__(self) -> None:
        if self.traffic_mb_month <= 0 or self.storage_gb_month <= 0:
            raise ValueError("traffic and storage budgets must be positive")


@dataclass(frozen=True)
class DataAcquisitionCharter:
    charter_id: str
    source: str
    metrics: tuple[str, ...]
    assets: tuple[str, ...]
    cadence: str
    timestamp_semantics: TimestampSemantics
    latency_sla: LatencySLA
    resource_budget: ResourceBudget
    owner: str
    revision_policy: str
    initial_scientific_state: ScientificState
    collector_version: str
    expected_schema_version: str
    retention_policy: Mapping[str, Any]
    quality_thresholds: Mapping[str, Any]
    created_at: datetime
    rationale: str
    schema_version: str = SCIENTIFIC_GOVERNANCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field in (
            "charter_id",
            "source",
            "cadence",
            "owner",
            "revision_policy",
            "collector_version",
            "expected_schema_version",
            "rationale",
        ):
            _required_text(getattr(self, field), field)
        if not self.metrics or not self.assets:
            raise ValueError("metrics and assets must not be empty")
        _jsonable(dict(self.retention_policy), "retention_policy")
        if self.initial_scientific_state is not ScientificState.COLLECTION_ONLY:
            raise ValueError("new acquisition charters must start in COLLECTION_ONLY")
        _jsonable(dict(self.quality_thresholds), "quality_thresholds")
        object.__setattr__(self, "created_at", _aware(self.created_at, "created_at"))

    def to_dict(self) -> dict[str, Any]:
        row = asdict(self)
        row["created_at"] = iso_z(self.created_at)
        return row

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> DataAcquisitionCharter:
        from predictor_core.kernel.timeindex import parse_iso

        row = dict(value)
        row["metrics"] = tuple(row["metrics"])
        row["assets"] = tuple(row["assets"])
        row["created_at"] = parse_iso(row["created_at"])
        row["timestamp_semantics"] = TimestampSemantics(**row["timestamp_semantics"])
        row["latency_sla"] = LatencySLA(**row["latency_sla"])
        row["resource_budget"] = ResourceBudget(**row["resource_budget"])
        row["initial_scientific_state"] = ScientificState(row["initial_scientific_state"])
        try:
            return cls(**row)
        except TypeError as exc:
            raise ValueError(f"invalid acquisition charter fields: {exc}") from exc


@dataclass(frozen=True)
class DatasetFreeze:
    freeze_id: str
    hypothesis_id: str
    dataset_frozen_at: datetime
    period_start: datetime
    period_end: datetime
    oos_cutoff: datetime
    assets: tuple[str, ...]
    sources: tuple[str, ...]
    metrics: tuple[str, ...]
    features: tuple[str, ...]
    feature_code_version: str
    charter_hashes: Mapping[str, str]
    hypothesis_registry_hash: str
    collector_versions: Mapping[str, str]
    schema_versions: Mapping[str, str]
    partition_hashes: Mapping[str, str]
    partition_roles: Mapping[str, str]
    exclusion_policy: Mapping[str, Any]
    manifest_hash: str = ""
    schema_version: str = SCIENTIFIC_GOVERNANCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _required_text(self.freeze_id, "freeze_id")
        _required_text(self.hypothesis_id, "hypothesis_id")
        _required_text(self.feature_code_version, "feature_code_version")
        _sha256(self.hypothesis_registry_hash, "hypothesis_registry_hash")
        for field in ("dataset_frozen_at", "period_start", "period_end", "oos_cutoff"):
            object.__setattr__(self, field, _aware(getattr(self, field), field))
        if not self.period_start < self.oos_cutoff < self.period_end:
            raise ValueError("oos_cutoff must be strictly inside the dataset period")
        if not all((self.assets, self.sources, self.metrics, self.features, self.partition_hashes)):
            raise ValueError(
                "assets, sources, metrics, features and partition_hashes must not be empty"
            )
        for charter_id, digest in self.charter_hashes.items():
            _required_text(charter_id, "charter_id")
            _sha256(digest, f"charter_hashes[{charter_id!r}]")
        if not self.charter_hashes:
            raise ValueError("charter_hashes must not be empty")
        for partition, digest in self.partition_hashes.items():
            _required_text(partition, "partition")
            _sha256(digest, f"partition_hashes[{partition!r}]")
        if set(self.partition_roles) != set(self.partition_hashes):
            raise ValueError("partition_roles must classify every partition hash exactly once")
        if set(self.partition_roles.values()) != {"IS", "OOS"}:
            raise ValueError("partition_roles must include both IS and OOS")
        _jsonable(dict(self.exclusion_policy), "exclusion_policy")
        if self.manifest_hash:
            _sha256(self.manifest_hash, "manifest_hash")

    def _unsigned_dict(self) -> dict[str, Any]:
        row = asdict(self)
        row.pop("manifest_hash")
        for field in ("dataset_frozen_at", "period_start", "period_end", "oos_cutoff"):
            row[field] = iso_z(getattr(self, field))
        return row

    def computed_hash(self) -> str:
        encoded = json.dumps(
            self._unsigned_dict(),
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def seal(self) -> DatasetFreeze:
        if self.manifest_hash and not self.verify():
            raise ValueError("freeze already contains an invalid manifest_hash")
        return replace(self, manifest_hash=self.computed_hash())

    def verify(self) -> bool:
        return bool(self.manifest_hash) and self.manifest_hash == self.computed_hash()

    def to_dict(self) -> dict[str, Any]:
        return {**self._unsigned_dict(), "manifest_hash": self.manifest_hash}


__all__ = [
    "SCIENTIFIC_GOVERNANCE_SCHEMA_VERSION",
    "DataAcquisitionCharter",
    "DatasetFreeze",
    "TimestampSemantics",
    "LatencySLA",
    "ResourceBudget",
    "ScientificState",
    "ScientificTransitionError",
    "validate_scientific_transition",
]
