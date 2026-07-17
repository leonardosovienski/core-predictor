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
