"""PredictionPoint — contrato do ciclo previsão → maturação → resultado."""
from datetime import datetime, timedelta, timezone

import pytest

from predictor_core.data.contracts import PredictionPoint

_T0 = datetime(2026, 7, 9, 12, 0, tzinfo=timezone.utc)


def test_ciclo_basico():
    pp = PredictionPoint(predicted_at=_T0, matures_at=_T0 + timedelta(days=7),
                         value=0.62, metadata={"asset": "BTCUSDT"})
    assert not pp.is_mature(_T0 + timedelta(days=6))
    assert pp.is_mature(_T0 + timedelta(days=7))          # fronteira inclusiva
    assert pp.metadata["asset"] == "BTCUSDT"


def test_maturacao_antes_da_emissao_e_lookahead():
    with pytest.raises(ValueError, match="lookahead"):
        PredictionPoint(predicted_at=_T0, matures_at=_T0 - timedelta(seconds=1),
                        value=1.0)


def test_imutavel():
    pp = PredictionPoint(predicted_at=_T0, matures_at=_T0, value="over")
    with pytest.raises(AttributeError):
        pp.value = "under"


def test_maturacao_instantanea_permitida():
    """matures_at == predicted_at é válido (resultado observável na emissão)."""
    pp = PredictionPoint(predicted_at=_T0, matures_at=_T0, value=1)
    assert pp.is_mature(_T0)


def test_metadata_mutada_apos_construcao_nao_vaza_para_o_objeto():
    # Regressão (auditoria hostil 2026-07-17): frozen=True só impede REBIND;
    # o dict passado em metadata continuava sendo a MESMA referência, então
    # mutá-lo depois da construção alterava o PredictionPoint "imutável" já
    # em uso por outro código.
    meta = {"asset": "BTCUSDT"}
    pp = PredictionPoint(predicted_at=_T0, matures_at=_T0, value=1, metadata=meta)
    meta["asset"] = "ETHUSDT"
    meta["future_price"] = 99999
    assert pp.metadata["asset"] == "BTCUSDT"
    assert "future_price" not in pp.metadata


def test_value_lista_mutada_apos_construcao_nao_vaza_para_o_objeto():
    valor = [1, 2, 3]
    pp = PredictionPoint(predicted_at=_T0, matures_at=_T0, value=valor)
    valor.append(999)
    assert pp.value == [1, 2, 3]


def test_value_escalar_nao_e_afetado_pela_copia_defensiva():
    pp = PredictionPoint(predicted_at=_T0, matures_at=_T0, value=0.73)
    assert pp.value == 0.73


def test_predicted_at_string_e_rejeitado_com_typeerror_claro():
    # Regressão (auditoria hostil 2026-07-17): antes, uma string ISO passava
    # sem checagem e o invariante virava comparação lexicográfica de string.
    with pytest.raises(TypeError, match="predicted_at deve ser datetime"):
        PredictionPoint(predicted_at="2026-07-09T12:00:00+00:00", matures_at=_T0, value=1)


def test_matures_at_string_e_rejeitado_com_typeerror_claro():
    with pytest.raises(TypeError, match="matures_at deve ser datetime"):
        PredictionPoint(predicted_at=_T0, matures_at="2026-07-09T12:00:00+00:00", value=1)


def test_naive_vs_aware_e_rejeitado_com_valueerror_claro_nao_typeerror_cru():
    naive = datetime(2026, 7, 9, 12, 0)  # sem tzinfo
    with pytest.raises(ValueError, match="naive e timezone-aware"):
        PredictionPoint(predicted_at=_T0, matures_at=naive, value=1)
    with pytest.raises(ValueError, match="naive e timezone-aware"):
        PredictionPoint(predicted_at=naive, matures_at=_T0, value=1)


def test_dois_naive_consistentes_sao_aceitos():
    # A checagem é sobre MISTURA de regimes, não uma exigência de que tudo
    # seja aware — dois naive comparáveis continuam válidos.
    naive_early = datetime(2026, 7, 9, 12, 0)
    naive_late = datetime(2026, 7, 9, 13, 0)
    pp = PredictionPoint(predicted_at=naive_early, matures_at=naive_late, value=1)
    assert pp.matures_at == naive_late


def test_hash_sempre_funciona_independente_de_metadata_ou_value_serem_dict():
    # Regressão: o __hash__ auto-gerado incluía metadata/value, então
    # hash(pp) funcionava ou lançava TypeError dependendo do CONTEÚDO em
    # runtime — comportamento inconsistente. Agora é sempre hasheável.
    com_dict_metadata = PredictionPoint(predicted_at=_T0, matures_at=_T0, value=1,
                                        metadata={"asset": "BTCUSDT"})
    com_dict_value = PredictionPoint(predicted_at=_T0, matures_at=_T0, value=[1, 2, 3])
    hash(com_dict_metadata)  # não levanta
    hash(com_dict_value)     # não levanta
    assert {com_dict_metadata, com_dict_value}  # usável em set


def test_hash_consistente_com_eq_para_objetos_iguais():
    a = PredictionPoint(predicted_at=_T0, matures_at=_T0, value=1, metadata={"x": 1})
    b = PredictionPoint(predicted_at=_T0, matures_at=_T0, value=1, metadata={"x": 1})
    assert a == b
    assert hash(a) == hash(b)
