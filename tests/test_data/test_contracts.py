"""contracts — invariantes temporais falham EXPLÍCITO (não em silêncio)."""
from datetime import datetime, timedelta, timezone

import pytest

from predictor_core.data.contracts import MarketDataPoint, SignalPoint

T0 = datetime(2026, 7, 3, 12, 0, 0, tzinfo=timezone.utc)


def _mdp(**kw):
    base = dict(symbol="bitcoin", timestamp=T0, open=1.0, high=2.0, low=0.5,
                close=1.5, volume=100.0, source="binance", interval="1d",
                published_at=T0)
    base.update(kw)
    return MarketDataPoint(**base)


def test_market_data_point_valid():
    p = _mdp()
    assert p.symbol == "bitcoin" and p.close == 1.5


def test_market_data_point_high_below_low_raises():
    with pytest.raises(ValueError):
        _mdp(high=0.4, low=0.5)


def test_market_data_point_published_before_timestamp_raises():
    with pytest.raises(ValueError):
        _mdp(published_at=T0 - timedelta(hours=1))


def test_market_data_point_rejects_naive_timestamp():
    with pytest.raises(ValueError, match="timezone"):
        _mdp(timestamp=datetime(2026, 7, 3, 12, 0))


def test_market_data_point_frozen():
    p = _mdp()
    with pytest.raises(Exception):
        p.close = 9.9  # frozen dataclass


def test_signal_point_valid_with_vintage():
    s = SignalPoint(name="fear_greed", timestamp=T0, value=55.0, source="alt.me",
                    published_at=T0 + timedelta(hours=1), vintage=T0 + timedelta(hours=1))
    assert s.value == 55.0 and s.reference_date is None


def test_signal_point_published_before_timestamp_raises():
    with pytest.raises(ValueError):
        SignalPoint(name="ipca", timestamp=T0, value=1.0, source="bcb",
                    published_at=T0 - timedelta(days=1))
