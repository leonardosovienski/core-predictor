"""asof — reconstrução forward-only de estado ("o que eu sabia em t")."""

from datetime import date, timedelta

from predictor_core.data.asof import state_asof


def _count(prefix):
    return len(prefix)


# eventos (timestamp, payload) ordenados; usados por vários testes
EVENTS = [(date(2020, 1, i), i) for i in range(1, 11)]  # 2020-01-01 .. 2020-01-10


def test_prefix_is_strictly_before_date():
    out = state_asof(EVENTS, _count, [date(2020, 1, 5)])
    assert out[date(2020, 1, 5)] == 4  # dias 1..4 (o dia 5 NÃO entra: forward-only)


def test_inclusive_includes_the_date():
    out = state_asof(EVENTS, _count, [date(2020, 1, 5)], inclusive=True)
    assert out[date(2020, 1, 5)] == 5  # dias 1..5


def test_event_at_or_after_date_never_leaks():
    # estado em datas crescentes é monotônico não-decrescente e nunca vê o futuro
    dates = [date(2020, 1, d) for d in (2, 6, 11)]
    out = state_asof(EVENTS, _count, dates)
    assert out[date(2020, 1, 2)] == 1
    assert out[date(2020, 1, 6)] == 5
    assert out[date(2020, 1, 11)] == 10  # todos os 10 já são passado


def test_window_excludes_stale_events():
    # janela de 3 dias antes da data: em 2020-01-08, só entram eventos com ts >= 01-05
    out = state_asof(EVENTS, _count, [date(2020, 1, 8)], window=timedelta(days=3))
    # ts < 08 e ts >= 05 → dias 5,6,7 = 3 eventos
    assert out[date(2020, 1, 8)] == 3


def test_key_callable_extracts_timestamp():
    events = [{"t": date(2020, 1, i), "v": i} for i in range(1, 6)]
    out = state_asof(events, _count, [date(2020, 1, 4)], key=lambda e: e["t"])
    assert out[date(2020, 1, 4)] == 3


def test_reducer_receives_the_prefix():
    # reducer arbitrário: soma dos payloads anteriores (generaliza ratings_asof)
    out = state_asof(EVENTS, lambda p: sum(v for _t, v in p), [date(2020, 1, 4)])
    assert out[date(2020, 1, 4)] == 1 + 2 + 3
