"""trials — registro com governança N+1, schema, trava de poder e DSR.

Reconciliação 2026-07-09: a versão evoluída do previsao-cripto virou a canônica.
Os testes de mecânica do registro usam power_attestation=False (bypass explícito
— aqui testamos o REGISTRO, não o harness); a trava tem testes próprios abaixo.
"""
import math

import pytest

from predictor_core.measurement.trials import (
    TrialRegistry, PowerAttestationMissingError, attestation_path_for,
    register_trial, load_trials, validate_trials,
    expected_max_sharpe, deflated_sharpe_ratio,
)
from predictor_core.testing.harness import attest_pipeline_power

# Retornos com Sharpe por-período MODESTO (~0.14) — PSR sensível, não saturado em 1.0.
_RETURNS = [0.001 + 0.01 * math.sin(i / 2.0) for i in range(150)]
_NOGATE = {"power_attestation": False}


def test_register_and_load(tmp_path):
    p = tmp_path / "trials.json"
    register_trial("v1", params={"h": 7}, sharpe=0.1, path=p,
                   now="2026-07-03T00:00:00Z", **_NOGATE)
    register_trial("v2", params={"h": 30}, sharpe=0.2, path=p,
                   now="2026-07-03T00:01:00Z", **_NOGATE)
    trials = load_trials(p)
    assert [t["name"] for t in trials] == ["v1", "v2"]


def test_reregister_same_name_updates_not_appends(tmp_path):
    p = tmp_path / "trials.json"
    register_trial("v1", params={"h": 7}, sharpe=0.1, path=p,
                   now="2026-01-01T00:00:00Z", **_NOGATE)
    # update de trial EXISTENTE não passa pela trava (maturação automática)
    register_trial("v1", params={"h": 7}, sharpe=0.9, path=p,
                   now="2026-02-01T00:00:00Z")
    trials = load_trials(p)
    assert len(trials) == 1
    assert trials[0]["sharpe"] == 0.9                      # valor atualizado
    assert trials[0]["registered_at"] == "2026-01-01T00:00:00Z"   # data original preservada


# --- governança de identidade (N+1) — promovida do previsao-cripto ------------

def test_mudar_params_de_trial_existente_e_erro(tmp_path):
    p = tmp_path / "trials.json"
    register_trial("t-a", params={"h": 7}, path=p, **_NOGATE)
    with pytest.raises(ValueError, match="tentativa nova"):
        register_trial("t-a", params={"h": 30}, path=p, **_NOGATE)
    assert load_trials(p)[0]["params"] == {"h": 7}         # nada gravado


def test_registro_invalido_nao_e_gravado(tmp_path):
    p = tmp_path / "trials.json"
    with pytest.raises(ValueError, match="schema"):
        register_trial("t-a", params={}, path=p, **_NOGATE)  # params vazio
    assert load_trials(p) == []


def test_campos_opcionais_do_schema(tmp_path):
    p = tmp_path / "trials.json"
    register_trial("t-a", params={"h": 7}, path=p,
                   features_used=["rsi"], test_period=["2026-07-01", "2026-07-31"],
                   **_NOGATE)
    t = load_trials(p)[0]
    assert t["features_used"] == ["rsi"]
    assert validate_trials(load_trials(p)) == []


@pytest.mark.parametrize("mutacao,erro", [
    ({"name": "com espaço"}, "name inválido"),
    ({"registered_at": "2026-07-07"}, "registered_at inválido"),
    ({"params": {}}, "params precisa ser dict NÃO-vazio"),
    ({"sharpe": float("nan")}, "sharpe inválido"),
    ({"notes": 42}, "notes precisa ser str"),
])
def test_schema_rejeita_campo_invalido(mutacao, erro):
    trial = {"name": "t1", "registered_at": "2026-07-07T00:00:00Z",
             "params": {"a": 1}, "sharpe": None, "notes": "", **mutacao}
    assert any(erro in e for e in validate_trials([trial]))


# --- trava de poder (harness ↔ registry) ---------------------------------------

def _eval_mean(series):
    m = sum(series) / len(series)
    return {"verdict": "COMPROVADA" if m > 0.5 else "REFUTADA"}


def test_trial_nova_sem_atestado_e_barrada(tmp_path):
    p = tmp_path / "trials.json"
    with pytest.raises(PowerAttestationMissingError, match="controle positivo"):
        register_trial("t-a", params={"h": 7}, path=p)
    assert load_trials(p) == []


def test_atestado_do_harness_destrava_o_registro(tmp_path):
    p = tmp_path / "trials.json"
    rec = attest_pipeline_power(
        _eval_mean, lambda: [1.0] * 10, lambda: [0.0] * 10,
        attestation_path=attestation_path_for(p), note="teste")
    assert rec["passed_at"]
    register_trial("t-a", params={"h": 7}, path=p)   # agora passa
    assert load_trials(p)[0]["name"] == "t-a"


def test_harness_reprovado_nao_emite_atestado(tmp_path):
    from predictor_core.testing.harness import PipelineHasNoPowerError
    p = tmp_path / "trials.json"
    ap = attestation_path_for(p)
    with pytest.raises(PipelineHasNoPowerError):
        # pipeline cego: nunca detecta o edge
        attest_pipeline_power(lambda s: {"verdict": "REFUTADA"},
                              lambda: [1.0] * 10, lambda: [0.0] * 10,
                              attestation_path=ap)
    assert not ap.exists()


def test_atestado_corrompido_nao_destrava(tmp_path):
    p = tmp_path / "trials.json"
    attestation_path_for(p).write_text("não-é-json", encoding="utf-8")
    with pytest.raises(PowerAttestationMissingError):
        register_trial("t-a", params={"h": 7}, path=p)


# --- DSR -----------------------------------------------------------------------

def test_expected_max_sharpe_grows_with_n():
    e5 = expected_max_sharpe(5, 0.04)
    e50 = expected_max_sharpe(50, 0.04)
    assert expected_max_sharpe(1, 0.04) == 0.0            # 1 tentativa: sem seleção
    assert e50 > e5 > 0.0                                  # mais tentativas → benchmark maior


def test_dsr_decreases_with_more_trials():
    dsr_few = deflated_sharpe_ratio(_RETURNS, [0.1, 0.12])
    dsr_many = deflated_sharpe_ratio(
        _RETURNS, [0.1, 0.12, 0.2, -0.1, 0.3, 0.25, -0.2, 0.4])
    assert dsr_many["sr0"] > dsr_few["sr0"]               # mais tentativas → SR0 maior
    assert dsr_many["dsr"] < dsr_few["dsr"]               # → DSR menor (mais exigente)


def test_registry_facade_deflates_by_registered_trials(tmp_path):
    reg = TrialRegistry(tmp_path / "trials.json")
    for i, s in enumerate([0.1, 0.2, 0.3, -0.1, 0.25]):
        reg.register(f"cfg{i}", params={"i": i}, sharpe=s,
                     now="2026-07-03T00:00:00Z", power_attestation=False)
    out = reg.deflated_sharpe(_RETURNS)
    assert out["n_trials"] == 5 and 0.0 <= out["dsr"] <= 1.0
    assert reg.validate() == []
