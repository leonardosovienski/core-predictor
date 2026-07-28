"""aggregation — fusão multi-fonte e TWAP (puros, determinísticos)."""
from datetime import datetime, timedelta

import pytest

from predictor_core.data.aggregation import consensus_median, consensus_mean, twap
from predictor_core.data.contracts import MarketDataPoint

T0 = datetime(2026, 7, 3, 0, 0, 0)


def _p(ts, close, pub=None, src="x"):
    return MarketDataPoint(symbol="btc", timestamp=ts, open=close, high=close + 1,
                           low=close - 1, close=close, volume=10.0, source=src,
                           interval="1d", published_at=pub or ts)


def test_consensus_median_fuses_per_timestamp():
    a = [_p(T0, 100.0), _p(T0 + timedelta(days=1), 110.0)]
    b = [_p(T0, 102.0), _p(T0 + timedelta(days=1), 120.0)]
    c = [_p(T0, 104.0), _p(T0 + timedelta(days=1), 112.0)]
    fused = consensus_median([a, b, c])
    assert [p.close for p in fused] == [102.0, 112.0]     # mediana ponto-a-ponto
    assert all(p.source == "consensus_median" for p in fused)


def test_consensus_published_at_is_max():
    # o consolidado só fica disponível quando a ÚLTIMA fonte publicou (anti-lookahead)
    late = T0 + timedelta(hours=5)
    a = [_p(T0, 100.0, pub=T0)]
    b = [_p(T0, 100.0, pub=late)]
    fused = consensus_mean([a, b])
    assert fused[0].published_at == late


def test_twap_uniform_grid_equals_mean_close():
    pts = [_p(T0 + timedelta(days=i), 100.0 + i) for i in range(4)]  # 100,101,102,103
    assert twap(pts) == pytest.approx(101.5, abs=0.5)


def test_twap_empty_raises():
    with pytest.raises(ValueError):
        twap([])
