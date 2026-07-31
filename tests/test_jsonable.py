"""to_jsonable — o caminho sancionado de volta do congelamento dos contratos."""
import json

import pytest

from predictor_core.contracts import to_jsonable
from predictor_core.data.contracts import _freeze
from predictor_core.kernel.jsonable import stable_sorted


def test_round_trip_desfaz_o_freeze_recursivamente():
    """_freeze congela; to_jsonable devolve tipos JSON nativos equivalentes."""
    original = {"prob": 0.48, "favorito": "Gen.G",
                "tags": ["a", "b"],
                "aninhado": {"k": [1, 2], "vazio": {}}}
    assert to_jsonable(_freeze(original)) == original


def test_o_resultado_e_serializavel_sem_default():
    """O ponto do helper: depois dele, json.dumps funciona SEM default=."""
    congelado = _freeze({"v": {"x": [1, 2]}, "s": {"b", "a"}})
    with pytest.raises(TypeError):
        json.dumps(congelado)                      # antes: mappingproxy
    assert json.loads(json.dumps(to_jsonable(congelado))) == {
        "v": {"x": [1, 2]}, "s": ["a", "b"]}


def test_conjunto_heterogeneo_tem_ordem_estavel():
    """A ordem não pode depender do PYTHONHASHSEED — o ledger é reproduzível."""
    assert stable_sorted(frozenset({1, "a", "b", 2})) == ["a", "b", 1, 2]
    assert to_jsonable(frozenset({3, 1, 2})) == [1, 2, 3]


def test_valores_desconhecidos_passam_intactos():
    """to_jsonable NÃO inventa serialização para tipos que o json não conhece —
    isso continua sendo erro explícito na hora de gravar."""
    sentinela = object()
    assert to_jsonable(sentinela) is sentinela
    assert to_jsonable({"o": sentinela})["o"] is sentinela
