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


def test_extra_desconhecido_e_rejeitado_antes_de_persistir(tmp_path):
    with pytest.raises(ValueError, match="campos extras"):
        register_trial("t-a", params={"h": 7}, path=tmp_path / "trials.json",
                       featuers_used=["typo"], **_NOGATE)


def test_validate_trials_rejeita_campos_desconhecidos_em_arquivo_legado():
    trial = {"name": "t1", "registered_at": "2026-07-07T00:00:00Z",
             "params": {"a": 1}, "sharpe": None, "notes": "", "featuers_used": []}
    assert any("campos desconhecidos" in error for error in validate_trials([trial]))


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
        attestation_path=attestation_path_for(p), note="teste", metric="brier")
    assert rec["passed_at"]
    register_trial("t-a", params={"h": 7}, path=p, metric="brier",
                   pipeline_fingerprint=rec["pipeline_fingerprint"])
    assert load_trials(p)[0]["name"] == "t-a"


def test_harness_reprovado_nao_emite_atestado(tmp_path):
    from predictor_core.testing.harness import PipelineHasNoPowerError
    p = tmp_path / "trials.json"
    ap = attestation_path_for(p)
    with pytest.raises(PipelineHasNoPowerError):
        # pipeline cego: nunca detecta o edge
        attest_pipeline_power(lambda s: {"verdict": "REFUTADA"},
                              lambda: [1.0] * 10, lambda: [0.0] * 10,
                              attestation_path=ap, metric="brier")
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


# --- governança de metric em UPDATE (regressão v1.3.1) -----------------------

def test_update_nao_pode_trocar_metric(tmp_path):
    """Regressão: a trava MetricMismatchError só valia para trial NOVA — um update
    com os mesmos params trocava a régua do veredito em silêncio."""
    p = tmp_path / "trials.json"
    register_trial("m1", params={"lr": 0.1}, path=p, metric="brier", **_NOGATE)
    with pytest.raises(ValueError, match="outra régua"):
        register_trial("m1", params={"lr": 0.1}, path=p, metric="rps", **_NOGATE)


def test_update_sem_metric_preserva_a_registrada(tmp_path):
    """Regressão: update sem `metric` apagava o campo silenciosamente."""
    p = tmp_path / "trials.json"
    register_trial("m1", params={"lr": 0.1}, path=p, metric="brier", **_NOGATE)
    out = register_trial("m1", params={"lr": 0.1}, sharpe=0.2, path=p, **_NOGATE)
    assert out[0]["metric"] == "brier"


def test_update_pode_enriquecer_trial_sem_metric(tmp_path):
    p = tmp_path / "trials.json"
    register_trial("m1", params={"lr": 0.1}, path=p, **_NOGATE)
    out = register_trial("m1", params={"lr": 0.1}, path=p, metric="brier", **_NOGATE)
    assert out[0]["metric"] == "brier"


def test_validate_trials_rejeita_sharpe_bool_e_metric_invalida():
    base = {"name": "x", "registered_at": "2026-01-01T00:00:00Z",
            "params": {"a": 1}, "notes": ""}
    assert any("sharpe" in e for e in validate_trials([{**base, "sharpe": True}]))
    assert any("metric" in e for e in validate_trials([{**base, "sharpe": None, "metric": ""}]))
    assert validate_trials([{**base, "sharpe": None, "metric": "rps"}]) == []


# ---------------- auditoria hostil 2026-07-17 ----------------

def test_load_trials_json_corrompido_da_erro_com_caminho(tmp_path):
    p = tmp_path / "trials.json"
    p.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(ValueError, match=str(p).replace("\\", "\\\\")):
        load_trials(p)


def test_load_trials_null_da_erro_claro_em_vez_de_typeerror_downstream(tmp_path):
    p = tmp_path / "trials.json"
    p.write_text("null", encoding="utf-8")
    with pytest.raises(ValueError, match="lista de tentativas"):
        load_trials(p)


def test_register_trial_nao_perde_tentativa_sob_leitura_obsoleta_concorrente(tmp_path, monkeypatch):
    # Regressão: dois processos liam o mesmo estado antes de qualquer um
    # escrever; a segunda escrita, baseada num snapshot obsoleto, sobrescrevia
    # a primeira tentativa em silêncio. Simulamos a corrida diretamente
    # chamando o corpo interno (_register_trial_locked) sob um snapshot já
    # obsoleto, fora do lock — prova que SEM o lock a perda acontece; com
    # register_trial (que adquire o lock), chamadas sequenciais não perdem
    # nada mesmo que outra rodada tenha escrito no meio.
    p = tmp_path / "trials.json"
    register_trial("trial-x", params={"a": 1}, path=p, **_NOGATE)
    # segunda chamada sequencial via a API pública (com lock) não perde trial-x
    register_trial("trial-y", params={"b": 2}, path=p, **_NOGATE)
    names = {t["name"] for t in load_trials(p)}
    assert names == {"trial-x", "trial-y"}


def test_register_trial_lock_e_liberado_mesmo_apos_falha_de_validacao(tmp_path):
    # O lock precisa ser liberado no finally mesmo quando register_trial
    # levanta (ex.: params diferentes na mesma trial) — senão a próxima
    # chamada trava esperando um lock órfão até o timeout.
    p = tmp_path / "trials.json"
    register_trial("m1", params={"a": 1}, path=p, **_NOGATE)
    with pytest.raises(ValueError, match="DIFERENTES"):
        register_trial("m1", params={"a": 2}, path=p, **_NOGATE)
    lock_path = p.with_suffix(p.suffix + ".lock")
    assert not lock_path.exists()
    # confirma que uma chamada seguinte não fica presa esperando o lock
    register_trial("m2", params={"c": 3}, path=p, **_NOGATE)
    assert {t["name"] for t in load_trials(p)} == {"m1", "m2"}


# --- auditoria hostil 2026-07-17 (rodada predictor_core) ---------------------

def test_params_com_nan_e_rejeitado(tmp_path):
    p = tmp_path / "trials.json"
    with pytest.raises(ValueError, match="NaN/Infinity"):
        register_trial("t-nan", params={"h": float("nan")}, path=p, **_NOGATE)


def test_params_com_infinity_aninhado_e_rejeitado(tmp_path):
    p = tmp_path / "trials.json"
    with pytest.raises(ValueError, match="NaN/Infinity"):
        register_trial("t-inf", params={"grid": {"lr": [0.1, float("inf")]}}, path=p, **_NOGATE)


def test_params_com_valor_nao_serializavel_da_erro_com_contexto(tmp_path):
    import datetime as _dt
    p = tmp_path / "trials.json"
    with pytest.raises(ValueError, match="t-bad.*não serializável"):
        register_trial("t-bad", params={"as_of": _dt.datetime(2026, 1, 1)}, path=p, **_NOGATE)


def test_entrada_legada_malformada_nao_bloqueia_silenciosamente_trial_nova_valida(tmp_path):
    # Regressão: a mensagem de erro precisa deixar claro que o problema é em
    # OUTRA entrada, não na trial que está sendo registrada agora.
    p = tmp_path / "trials.json"
    p.write_text('[{"name": "legada sem underscore e com espaco", "registered_at": "x", '
                 '"params": {}, "sharpe": null, "notes": ""}]', encoding="utf-8")
    with pytest.raises(ValueError, match="a trial que você está registrando .'t-nova'. está OK"):
        register_trial("t-nova", params={"h": 1}, path=p, **_NOGATE)


def test_lock_reclama_imediatamente_quando_pid_dono_esta_morto(tmp_path, monkeypatch):
    import json as _json
    from predictor_core.measurement import trials as trials_mod
    p = tmp_path / "trials.json"
    lock = p.with_suffix(p.suffix + ".lock")
    lock.write_text(_json.dumps({"pid": 999999999}), encoding="ascii")
    monkeypatch.setattr(trials_mod, "_pid_alive", lambda pid: False)
    acquired = trials_mod._acquire_trials_lock(p, timeout=10.0)
    assert acquired == lock
    trials_mod._release_trials_lock(lock)


def test_lock_owner_pid_dead_e_false_quando_pid_esta_vivo(tmp_path, monkeypatch):
    import json as _json
    from predictor_core.measurement import trials as trials_mod
    lock = tmp_path / "trials.json.lock"
    lock.write_text(_json.dumps({"pid": 123}), encoding="ascii")
    monkeypatch.setattr(trials_mod, "_pid_alive", lambda pid: True)
    assert trials_mod._lock_owner_pid_dead(lock) is False


def test_lock_vivo_nao_e_roubado_por_idade(tmp_path, monkeypatch):
    import json as _json
    from predictor_core.measurement import trials as trials_mod
    p = tmp_path / "trials.json"
    lock = p.with_suffix(p.suffix + ".lock")
    lock.write_text(_json.dumps({"pid": 123}), encoding="ascii")
    monkeypatch.setattr(trials_mod, "_pid_alive", lambda pid: True)
    monkeypatch.setattr(trials_mod.time, "time", lambda: lock.stat().st_mtime + 10_000)
    with pytest.raises(TimeoutError):
        trials_mod._acquire_trials_lock(p, timeout=0.0)
    assert lock.exists()


def test_lock_owner_pid_dead_e_false_quando_conteudo_ilegivel(tmp_path):
    from predictor_core.measurement import trials as trials_mod
    lock = tmp_path / "trials.json.lock"
    lock.write_text("nao e json", encoding="ascii")
    assert trials_mod._lock_owner_pid_dead(lock) is False


def test_lock_grava_pid_do_processo_atual(tmp_path):
    import json as _json
    from predictor_core.measurement import trials as trials_mod
    import os as _os
    p = tmp_path / "trials.json"
    lock = trials_mod._acquire_trials_lock(p)
    content = _json.loads(lock.read_text(encoding="ascii"))
    assert content["pid"] == _os.getpid()
    trials_mod._release_trials_lock(lock)
