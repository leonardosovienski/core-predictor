from datetime import UTC, datetime, timedelta

from predictor_core.contracts import SignalPoint
from predictor_core.data.source_quality import (
    SourceQualityState,
    SourceQualityThresholds,
    source_quality_scorecard,
)

T0 = datetime(2026, 1, 1, tzinfo=UTC)


def point(index, *, delay=10, content_hash="a" * 64, flags=frozenset()):
    event = T0 + timedelta(hours=index)
    published = event + timedelta(seconds=5)
    return SignalPoint(
        name="funding",
        timestamp=event,
        event_at=event,
        published_at=published,
        ingested_at=published + timedelta(seconds=delay),
        value=0.001,
        source="binance",
        instrument="BTCUSDT-PERP",
        metric="funding_rate",
        unit="ratio",
        content_hash=content_hash,
        collector_version="1.0.0",
        schema_version="signals/2",
        quality_flags=flags,
    )


def test_healthy_source_scorecard():
    result = source_quality_scorecard(
        [point(0), point(1), point(2)],
        source="binance",
        window_start=T0,
        window_end=T0 + timedelta(hours=3),
        cadence_seconds=3600,
        thresholds=SourceQualityThresholds(maximum_gap_seconds=0),
        successful_requests=3,
        total_requests=3,
    )
    assert result.state is SourceQualityState.HEALTHY
    assert result.coverage == 1 and result.gap_count == 0


def test_gaps_and_latency_degrade_but_bad_provenance_quarantines():
    limits = SourceQualityThresholds(
        minimum_coverage=0.9,
        maximum_median_freshness_seconds=20,
        maximum_p99_freshness_seconds=20,
        maximum_gap_count=0,
        maximum_gap_seconds=0,
    )
    degraded = source_quality_scorecard(
        [point(0, delay=100), point(2, delay=100)],
        source="binance",
        window_start=T0,
        window_end=T0 + timedelta(hours=3),
        cadence_seconds=3600,
        thresholds=limits,
        successful_requests=2,
        total_requests=3,
    )
    assert degraded.state is SourceQualityState.DEGRADED
    quarantined = source_quality_scorecard(
        [point(0, content_hash="", flags=frozenset({"published_at_untrusted"}))],
        source="binance",
        window_start=T0,
        window_end=T0 + timedelta(hours=1),
        cadence_seconds=3600,
        thresholds=limits,
        successful_requests=1,
        total_requests=1,
    )
    assert quarantined.state is SourceQualityState.QUARANTINED
    assert {"causality", "integrity"} <= set(quarantined.violations)


def test_revisions_and_reference_divergence_are_measured():
    first = point(0)
    revised = point(0, content_hash="b" * 64)
    result = source_quality_scorecard(
        [first, revised],
        source="binance",
        window_start=T0,
        window_end=T0 + timedelta(hours=1),
        cadence_seconds=3600,
        thresholds=SourceQualityThresholds(maximum_revision_rate=0),
        successful_requests=1,
        total_requests=1,
        reference_values={("BTCUSDT-PERP", "funding_rate", T0): 0.002},
    )
    assert result.revision_count == 1
    assert result.mean_divergence == 0.001
    assert result.state is SourceQualityState.DEGRADED
