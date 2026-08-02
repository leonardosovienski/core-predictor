"""kernel.jsonl_store — append-only, streaming, corrupção explícita."""

import pytest

from predictor_core.kernel.jsonl_store import JsonlStore


def test_append_and_iterate(tmp_path):
    store = JsonlStore(tmp_path / "events.jsonl")
    store.append({"kind": "bet", "stake": 10})
    store.append({"kind": "settle", "pnl": -10})
    assert list(store) == [{"kind": "bet", "stake": 10}, {"kind": "settle", "pnl": -10}]


def test_missing_file_iterates_empty(tmp_path):
    assert list(JsonlStore(tmp_path / "nope.jsonl")) == []


def test_count_and_tail(tmp_path):
    store = JsonlStore(tmp_path / "e.jsonl")
    for i in range(5):
        store.append({"i": i})
    assert store.count() == 5
    assert store.tail(2) == [{"i": 3}, {"i": 4}]
    assert store.tail(0) == []


def test_corrupted_line_raises_with_line_number(tmp_path):
    p = tmp_path / "bad.jsonl"
    p.write_text('{"ok": 1}\n{broken\n', encoding="utf-8")
    with pytest.raises(ValueError, match=":2:"):
        list(JsonlStore(p))


def test_unserializable_record_fails_before_write(tmp_path):
    store = JsonlStore(tmp_path / "e.jsonl")
    with pytest.raises(TypeError):
        store.append({"bad": object()})
    assert not store.path.exists()


def test_append_rejeita_nan_antes_de_abrir_o_arquivo(tmp_path):
    store = JsonlStore(tmp_path / "s.jsonl")
    with pytest.raises(ValueError):
        store.append({"x": float("nan")})
    assert not (tmp_path / "s.jsonl").exists()


def test_append_serializa_containers_congelados_do_core(tmp_path):
    """Os contratos do core congelam seus campos (data.contracts._freeze):
    dict vira MappingProxyType, list/tuple viram tuple e set vira frozenset.
    O JsonlStore é o gravador do PRÓPRIO core — gravar um campo congelado
    (ex.: PredictionPoint.value) precisa funcionar, senão duas APIs que
    existem para compor não compõem."""
    from predictor_core.data.contracts import _freeze

    store = JsonlStore(tmp_path / "frozen.jsonl")
    congelado = _freeze(
        {
            "probability_a": 0.4856,
            "favorite": "Gen.G",
            "tags": ["a", "b"],
            "aninhado": {"k": [1, 2]},
        }
    )
    store.append({"value": congelado, "conjunto": frozenset({"b", "a"})})

    assert list(store) == [
        {
            "value": {
                "probability_a": 0.4856,
                "favorite": "Gen.G",
                "tags": ["a", "b"],
                "aninhado": {"k": [1, 2]},
            },
            "conjunto": ["a", "b"],  # frozenset é ordenado para a linha ser determinística
        }
    ]


def test_append_ainda_rejeita_objeto_realmente_nao_serializavel(tmp_path):
    """O `default=` cobre só os containers imutáveis do core; qualquer outro
    tipo continua falhando ANTES de abrir o arquivo."""
    store = JsonlStore(tmp_path / "e.jsonl")
    with pytest.raises(TypeError):
        store.append({"bad": object()})
    assert not store.path.exists()


def test_append_de_frozenset_heterogeneo_e_deterministico(tmp_path):
    """`list(frozenset)` ordena pelo HASH — varia com o PYTHONHASHSEED e faria
    a MESMA entrada gerar linhas diferentes entre execuções. O ledger é a
    memória da governança: a linha precisa ser reproduzível."""
    store = JsonlStore(tmp_path / "s.jsonl")
    store.append({"misto": frozenset({1, "a", "b", 2})})
    # Ordem por repr: "'a'"/"'b'" (aspa, ASCII 39) vêm antes de "1"/"2". O
    # valor exato importa menos que ser SEMPRE o mesmo — rodar a suíte com
    # PYTHONHASHSEED variado não pode mudar esta linha.
    assert list(store) == [{"misto": ["a", "b", 1, 2]}]
