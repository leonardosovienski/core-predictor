"""router — fallback sequencial, consenso concorrente, circuit breaker (via asyncio.run)."""
import asyncio
from datetime import datetime

import pytest

from predictor_core.data.circuit_breaker import CircuitBreaker
from predictor_core.data.contracts import DataProvider, DataUnavailableError, MarketDataPoint
from predictor_core.data.router import AggregationRouter, FallbackRouter

T0 = datetime(2026, 7, 3)


def _pt(close, src):
    return MarketDataPoint(symbol="btc", timestamp=T0, open=close, high=close + 1,
                           low=close - 1, close=close, volume=1.0, source=src,
                           interval="1d", published_at=T0)


class _Provider(DataProvider):
    def __init__(self, name, close=None, fail=False):
        self.name = name
        self._close = close
        self._fail = fail
        self.calls = 0

    async def fetch_ohlcv(self, symbol, interval="1d", limit=1):
        self.calls += 1
        if self._fail:
            raise RuntimeError(f"{self.name} caiu")
        return [_pt(self._close, self.name)]

    async def health_check(self):
        return not self._fail


def test_fallback_uses_second_when_first_fails():
    p1, p2 = _Provider("a", fail=True), _Provider("b", close=100.0)
    router = FallbackRouter([p1, p2])
    out = asyncio.run(router.fetch_ohlcv("btc"))
    assert out[0].source == "b" and p1.calls == 1 and p2.calls == 1


def test_fallback_raises_when_all_fail():
    router = FallbackRouter([_Provider("a", fail=True), _Provider("b", fail=True)])
    with pytest.raises(DataUnavailableError):
        asyncio.run(router.fetch_ohlcv("btc"))


def test_fallback_skips_open_breaker_without_calling():
    p1, p2 = _Provider("a", close=1.0), _Provider("b", close=2.0)
    breaker = CircuitBreaker("a", failure_threshold=1, reset_timeout=999)
    breaker.record_failure()                       # abre o circuito de "a"
    router = FallbackRouter([p1, p2], breakers={"a": breaker})
    out = asyncio.run(router.fetch_ohlcv("btc"))
    assert out[0].source == "b" and p1.calls == 0  # "a" pulado sem gastar requisição


def test_aggregation_consenso_funde_sobreviventes():
    p1, p2, p3 = _Provider("a", close=100.0), _Provider("b", fail=True), _Provider("c", close=104.0)
    router = AggregationRouter([p1, p2, p3], policy="consensus_median")
    out = asyncio.run(router.fetch_ohlcv("btc"))
    assert out[0].close == 102.0                   # mediana de {100,104} sobreviventes


def test_aggregation_raises_when_all_fail():
    router = AggregationRouter([_Provider("a", fail=True)], policy="consensus_mean")
    with pytest.raises(DataUnavailableError):
        asyncio.run(router.fetch_ohlcv("btc"))


def test_router_rejects_empty_providers():
    with pytest.raises(ValueError):
        FallbackRouter([])
