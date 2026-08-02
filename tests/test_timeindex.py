"""kernel.timeindex — fronteira ISO/UTC: naive é erro, roundtrip é identidade."""

from datetime import UTC, datetime, timedelta, timezone

import pytest

from predictor_core.kernel.timeindex import NaiveDatetimeError, iso_z, parse_iso, to_utc, utcnow


def test_utcnow_is_aware_utc():
    now = utcnow()
    assert now.tzinfo is not None and now.utcoffset() == timedelta(0)


def test_to_utc_converts_offset():
    br = datetime(2026, 7, 11, 9, 0, tzinfo=timezone(timedelta(hours=-3)))
    assert to_utc(br).hour == 12


def test_to_utc_rejects_naive():
    with pytest.raises(NaiveDatetimeError):
        to_utc(datetime(2026, 7, 11))


def test_iso_z_format_matches_trials_schema():
    dt = datetime(2026, 7, 11, 12, 30, 45, tzinfo=UTC)
    s = iso_z(dt)
    assert s == "2026-07-11T12:30:45Z"
    datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")  # o formato que validate_trials exige


def test_parse_iso_roundtrip():
    dt = datetime(2026, 7, 11, 12, 30, 45, tzinfo=UTC)
    assert parse_iso(iso_z(dt)) == dt


def test_parse_iso_rejects_naive_string():
    with pytest.raises(NaiveDatetimeError):
        parse_iso("2026-07-11T12:30:45")
