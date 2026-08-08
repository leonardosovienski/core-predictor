"""Deterministic source-quality metrics for enriched SignalPoint series."""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import StrEnum
from statistics import fmean, median
from typing import Any

from predictor_core.data.contracts import SignalPoint
from predictor_core.kernel.timeindex import to_utc


class SourceQualityState(StrEnum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    QUARANTINED = "QUARANTINED"


@dataclass(frozen=True)
class SourceQualityThresholds:
    minimum_coverage: float = 0.99
    maximum_median_freshness_seconds: float = 60.0
    maximum_p99_freshness_seconds: float = 300.0
    maximum_gap_count: int = 0
    maximum_gap_seconds: float = 0.0
    maximum_revision_rate: float = 0.01
    maximum_divergence: float | None = None
    minimum_availability: float = 0.99
    maximum_causality_failure_rate: float = 0.0
    maximum_integrity_failure_rate: float = 0.0

    def __post_init__(self) -> None:
        rates = (
            self.minimum_coverage,
            self.maximum_revision_rate,
            self.minimum_availability,
            self.maximum_causality_failure_rate,
            self.maximum_integrity_failure_rate,
        )
        if any(not 0 <= value <= 1 for value in rates):
            raise ValueError("quality rates must be between zero and one")
        if (
            min(
                self.maximum_median_freshness_seconds,
                self.maximum_p99_freshness_seconds,
                self.maximum_gap_count,
                self.maximum_gap_seconds,
            )
            < 0
        ):
            raise ValueError("quality duration/count thresholds must not be negative")


@dataclass(frozen=True)
class SourceQualityScorecard:
    source: str
    window_start: datetime
    window_end: datetime
    expected_points: int
    observed_points: int
    successful_requests: int
    total_requests: int
    coverage: float
    freshness_median_seconds: float
    freshness_p99_seconds: float
    gap_count: int
    maximum_gap_seconds: float
    revision_count: int
    revision_rate: float
    mean_divergence: float | None
    availability: float
    causality_failure_rate: float
    integrity_failure_rate: float
    state: SourceQualityState
    violations: tuple[str, ...]
    thresholds: SourceQualityThresholds

    def to_dict(self) -> dict[str, Any]:
        row = asdict(self)
        row["window_start"] = self.window_start.isoformat()
        row["window_end"] = self.window_end.isoformat()
        row["state"] = self.state.value
        return row


def _quantile99(values: Sequence[float]) -> float:
    if not values:
        return math.inf
    ordered = sorted(values)
    return ordered[math.ceil(0.99 * len(ordered)) - 1]


def _apply_thresholds(
    *,
    coverage: float,
    freshness_median_seconds: float,
    freshness_p99_seconds: float,
    gap_count: int,
    maximum_gap_seconds: float,
    revision_rate: float,
    mean_divergence: float | None,
    availability: float,
    causality_failure_rate: float,
    integrity_failure_rate: float,
    limits: SourceQualityThresholds,
):
    degraded: list[str] = []
    quarantined: list[str] = []
    checks = {
        "coverage": coverage < limits.minimum_coverage,
        "freshness_median": freshness_median_seconds > limits.maximum_median_freshness_seconds,
        "freshness_p99": freshness_p99_seconds > limits.maximum_p99_freshness_seconds,
        "gaps": gap_count > limits.maximum_gap_count,
        "maximum_gap": maximum_gap_seconds > limits.maximum_gap_seconds,
        "revisions": revision_rate > limits.maximum_revision_rate,
        "availability": availability < limits.minimum_availability,
    }
    degraded.extend(name for name, failed in checks.items() if failed)
    if (
        limits.maximum_divergence is not None
        and mean_divergence is not None
        and mean_divergence > limits.maximum_divergence
    ):
        degraded.append("divergence")
    if causality_failure_rate > limits.maximum_causality_failure_rate:
        quarantined.append("causality")
    if integrity_failure_rate > limits.maximum_integrity_failure_rate:
        quarantined.append("integrity")
    violations = tuple(quarantined + degraded)
    state = (
        SourceQualityState.QUARANTINED
        if quarantined
        else SourceQualityState.DEGRADED
        if degraded
        else SourceQualityState.HEALTHY
    )
    return state, violations


def source_quality_scorecard(
    points: Iterable[SignalPoint],
    *,
    source: str,
    window_start: datetime,
    window_end: datetime,
    cadence_seconds: float,
    thresholds: SourceQualityThresholds,
    successful_requests: int,
    total_requests: int,
    reference_values: Mapping[tuple[str, str, datetime], float] | None = None,
) -> SourceQualityScorecard:
    start, end = to_utc(window_start), to_utc(window_end)
    if end <= start or cadence_seconds <= 0 or total_requests < successful_requests:
        raise ValueError("invalid scorecard window, cadence or request counts")

    def event_time(point: SignalPoint) -> datetime:
        assert point.event_at is not None
        return point.event_at

    def ingested_time(point: SignalPoint) -> datetime:
        assert point.ingested_at is not None
        return point.ingested_at

    selected = sorted(
        (point for point in points if point.source == source and start <= event_time(point) < end),
        key=event_time,
    )
    expected = max(1, math.ceil((end - start).total_seconds() / cadence_seconds))
    unique_keys = {(p.instrument, p.metric, event_time(p)) for p in selected}
    coverage = min(1.0, len(unique_keys) / expected)
    latencies = [(ingested_time(p) - p.published_at).total_seconds() for p in selected]
    event_times = sorted({event_time(p) for p in selected})
    gaps = [
        (right - left).total_seconds() - cadence_seconds
        for left, right in zip(event_times, event_times[1:])
        if (right - left).total_seconds() > cadence_seconds
    ]
    versions: dict[tuple[str, str, datetime], set[str]] = defaultdict(set)
    for point in selected:
        versions[(point.instrument, point.metric, event_time(point))].add(point.content_hash)
    revisions = sum(max(0, len(items) - 1) for items in versions.values())
    divergences = []
    if reference_values is not None:
        divergences = [
            abs(point.value - reference_values[key])
            for point in selected
            if (key := (point.instrument, point.metric, event_time(point))) in reference_values
        ]
    causality_failures = sum(
        "published_at_untrusted" in point.quality_flags or point.published_at < event_time(point)
        for point in selected
    )
    integrity_failures = sum(not point.is_enriched for point in selected)
    count = len(selected)
    freshness_median_seconds = median(latencies) if latencies else math.inf
    freshness_p99_seconds = _quantile99(latencies)
    gap_count = len(gaps)
    maximum_gap_seconds = max(gaps, default=0.0)
    revision_rate = revisions / max(1, len(unique_keys))
    mean_divergence = fmean(divergences) if divergences else None
    availability = successful_requests / max(1, total_requests)
    causality_failure_rate = causality_failures / max(1, count)
    integrity_failure_rate = integrity_failures / max(1, count)
    state, violations = _apply_thresholds(
        coverage=coverage,
        freshness_median_seconds=freshness_median_seconds,
        freshness_p99_seconds=freshness_p99_seconds,
        gap_count=gap_count,
        maximum_gap_seconds=maximum_gap_seconds,
        revision_rate=revision_rate,
        mean_divergence=mean_divergence,
        availability=availability,
        causality_failure_rate=causality_failure_rate,
        integrity_failure_rate=integrity_failure_rate,
        limits=thresholds,
    )
    return SourceQualityScorecard(
        source=source,
        window_start=start,
        window_end=end,
        expected_points=expected,
        observed_points=count,
        successful_requests=successful_requests,
        total_requests=total_requests,
        coverage=coverage,
        freshness_median_seconds=freshness_median_seconds,
        freshness_p99_seconds=freshness_p99_seconds,
        gap_count=gap_count,
        maximum_gap_seconds=maximum_gap_seconds,
        revision_count=revisions,
        revision_rate=revision_rate,
        mean_divergence=mean_divergence,
        availability=availability,
        causality_failure_rate=causality_failure_rate,
        integrity_failure_rate=integrity_failure_rate,
        state=state,
        violations=violations,
        thresholds=thresholds,
    )


__all__ = [
    "SourceQualityScorecard",
    "SourceQualityState",
    "SourceQualityThresholds",
    "source_quality_scorecard",
]
