"""quality — detecção de salto, inferência de split, série ajustada contínua."""
import pytest

from predictor_core.data.quality import (
    overnight_returns, detect_jumps, infer_split_factor, adjusted_closes,
)


def test_detect_jumps_flags_only_large_moves():
    dates = ["d0", "d1", "d2", "d3"]
    closes = [100.0, 101.0, 50.0, 51.0]        # queda de ~50% em d2
    jumps = detect_jumps(dates, closes, threshold=0.30)
    assert [d for d, _ in jumps] == ["d2"]


def test_infer_split_factor_split_and_grouping():
    assert infer_split_factor(100.0, 50.0) == pytest.approx(0.5)    # split 1:2 → ×0.5 antes
    assert infer_split_factor(50.0, 100.0) == pytest.approx(2.0)    # grupamento 2:1 → ×2
    assert infer_split_factor(100.0, 33.0) == pytest.approx(1 / 3, abs=1e-4)  # 1:3


def test_infer_split_factor_none_when_not_round():
    assert infer_split_factor(100.0, 73.0) is None  # proporção não-redonda → quarentena


def test_adjusted_closes_makes_series_continuous():
    dates = ["2020-01-01", "2020-06-01", "2021-01-01"]
    closes = [100.0, 50.0, 55.0]                # split 1:2 em 2020-06-01
    adj = adjusted_closes(dates, closes, [("2020-06-01", 0.5)])
    assert adj == [50.0, 50.0, 55.0]            # preços ANTES do ex_date ×0.5


def test_adjusted_closes_rejects_nonpositive_factor():
    with pytest.raises(ValueError):
        adjusted_closes(["d0", "d1"], [10.0, 10.0], [("d1", 0.0)])


def test_overnight_returns_skips_nonpositive_prev():
    out = overnight_returns(["a", "b", "c"], [0.0, 10.0, 11.0])
    assert [d for d, _ in out] == ["c"]         # b pulado (prev=0)


def test_overnight_returns_com_close_anterior_nan_produz_ret_nan_em_vez_de_omitir():
    # Regressão (auditoria hostil 2026-07-17): `closes[i-1] > 0` é sempre False
    # para NaN em Python — o par inteiro desaparecia da série de retornos, como
    # se faltasse um candle em vez de haver um candle corrompido.
    import math
    dates = ["d0", "d1", "d2"]
    closes = [100.0, float("nan"), 105.0]
    rets = overnight_returns(dates, closes)
    assert len(rets) == 2
    assert rets[0][0] == "d1" and math.isnan(rets[0][1])


def test_detect_jumps_sempre_reporta_nan_independente_do_threshold():
    import math
    dates = ["d0", "d1", "d2"]
    closes = [100.0, float("nan"), 102.0]
    jumps = detect_jumps(dates, closes, threshold=0.99)  # threshold alto, não pegaria por magnitude
    assert any(d == "d1" and math.isnan(r) for d, r in jumps)


def test_detect_jumps_serie_normal_sem_nan_nao_regride():
    # Guarda de não-regressão: série limpa continua sem falsos positivos.
    dates = ["d0", "d1", "d2"]
    closes = [100.0, 100.5, 101.0]
    assert detect_jumps(dates, closes, threshold=0.30) == []
