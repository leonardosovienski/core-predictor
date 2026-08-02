"""replay — anti-lookahead ESTRUTURAL: espiar o futuro deve ser impossível, não proibido."""

import pytest

from predictor_core.measurement import replay


def test_pastview_blocks_future_index():
    out = []

    def handler(past):
        out.append(len(past))  # tamanho = asof+1 (só o passado visível)
        with pytest.raises(replay.LookaheadError):
            _ = past[past.asof_index + 1]  # espiar amanhã
        return None

    replay.replay([10, 20, 30], handler)
    assert out == [1, 2, 3]


def test_pastview_nao_carrega_futuro_nem_no_atributo_privado():
    """O encapsulamento não pode ser a única barreira contra lookahead."""
    seen = []

    def handler(past):
        seen.append(tuple(past._data))

    replay.replay([10, 20, 30], handler)
    assert seen == [(10,), (10, 20), (10, 20, 30)]


def test_pastview_slice_clamps_to_past():
    seen = {}

    def handler(past):
        seen[past.asof_index] = list(past[:])  # slice nunca vaza o futuro
        return past.latest

    ledger = replay.replay([1, 2, 3], handler)
    assert seen[0] == [1] and seen[1] == [1, 2] and seen[2] == [1, 2, 3]
    assert ledger == [1, 2, 3]  # decisões não-None na ordem temporal


def test_replay_drops_none_decisions():
    ledger = replay.replay([1, 2, 3, 4], lambda p: p.latest if p.latest % 2 == 0 else None)
    assert ledger == [2, 4]


def test_replay_key_rejects_out_of_order():
    events = [("2024-01-01", 1), ("2024-01-03", 2), ("2024-01-02", 3)]  # fora de ordem
    with pytest.raises(ValueError):
        replay.replay(events, lambda p: None, key=lambda e: e[0])


def test_replay_key_accepts_monotonic():
    events = [("2024-01-01", 1), ("2024-01-02", 2), ("2024-01-03", 3)]
    ledger = replay.replay(events, lambda p: p.latest[1], key=lambda e: e[0])
    assert ledger == [1, 2, 3]


def test_pastview_negativo_alem_do_inicio_e_indexerror_nao_lookahead():
    """Regressão: past[-10] com 3 eventos levantava LookaheadError — acesso a
    passado inexistente não é lookahead; o diagnóstico do erro capital ficava poluído."""
    capturado = {}

    def handler(past):
        if past.asof_index == 2:
            with pytest.raises(IndexError):
                past[-10]
            with pytest.raises(replay.LookaheadError):
                past[4]
            capturado["ok"] = True
        return None

    replay.replay([(i, i) for i in range(5)], handler, key=lambda e: e[0])
    assert capturado.get("ok")
