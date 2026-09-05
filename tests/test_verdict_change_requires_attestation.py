"""Mudar o veredito de uma trial existente exige atestado, como criar uma nova.

Auditoria adversarial 2026-09-05, achado 3 (core-predictor#21). O gate de
atestação vivia no ramo `else` de um `for ... else`: só era avaliado quando o
`name` NÃO existia no registro. Com o mesmo `name` e os MESMOS `params`, o
caminho de atualização atravessava sem verificação nenhuma — uma trial
`refutada` virava `comprovada` sem controle positivo, e o estado anterior
desaparecia sem rastro.

Como `status` é o que o README e o HANDOFF do consumidor reportam, a alteração
seria invisível na leitura normal do projeto.

Duas regras entram aqui:
  1. mudou status ou sharpe -> é afirmação nova -> exige atestado válido;
  2. o veredito anterior é PRESERVADO em `superseded`, não sobrescrito.
"""

from __future__ import annotations

import pytest

from predictor_core import (
    PowerAttestationMissingError,
    attestation_path_for,
    load_trials,
    register_trial,
    validate_trials,
)
from predictor_core.testing.harness import attest_pipeline_power

_SEM_GATE = {"power_attestation": False}


def _eval_mean(series):
    mean = sum(series) / len(series)
    return {"verdict": "COMPROVADA" if mean > 0.5 else "REFUTADA"}


@pytest.fixture
def registro(tmp_path):
    """Trial `refutada` já registrada, sem atestado no diretório."""
    p = tmp_path / "trials.json"
    register_trial(
        "t-refutada",
        params={"h": 7},
        sharpe=0.07,
        metric="brier",
        status="refutada",
        notes="NO-GO: IC cruza zero",
        path=p,
        **_SEM_GATE,
    )
    return p


def _atesta(p, tmp_path):
    return attest_pipeline_power(
        _eval_mean,
        lambda: [1.0] * 10,
        lambda: [0.0] * 10,
        attestation_path=attestation_path_for(p),
        metric="brier",
        repo=tmp_path,
    )


def test_flip_de_veredito_sem_atestado_e_bloqueado(registro):
    """O ataque do achado 3, agora barrado."""
    with pytest.raises(PowerAttestationMissingError, match="mudança de veredito"):
        register_trial(
            "t-refutada",
            params={"h": 7},
            sharpe=0.07,
            metric="brier",
            status="comprovada",
            notes="reescrito",
            path=registro,
        )
    assert load_trials(registro)[0]["status"] == "refutada", "o veredito não pode ter mudado"


def test_sharpe_inflado_sem_atestado_e_bloqueado(registro):
    """Mudar só o número também é afirmação nova, não edição de comentário."""
    with pytest.raises(PowerAttestationMissingError):
        register_trial(
            "t-refutada",
            params={"h": 7},
            sharpe=9.99,
            metric="brier",
            status="refutada",
            path=registro,
        )
    assert load_trials(registro)[0]["sharpe"] == 0.07


def test_editar_apenas_notes_continua_livre(registro):
    """Corrigir um comentário não é produzir afirmação — não exige atestado."""
    register_trial(
        "t-refutada",
        params={"h": 7},
        sharpe=0.07,
        metric="brier",
        status="refutada",
        notes="mesma conclusão, redação corrigida",
        path=registro,
    )
    t = load_trials(registro)[0]
    assert t["notes"] == "mesma conclusão, redação corrigida"
    assert t["status"] == "refutada"
    assert "superseded" not in t, "sem mudança de veredito, não há histórico a criar"


def test_com_atestado_valido_o_flip_passa_e_preserva_o_anterior(registro, tmp_path):
    """A mudança legítima continua possível — e deixa rastro."""
    rec = _atesta(registro, tmp_path)
    register_trial(
        "t-refutada",
        params={"h": 7},
        sharpe=0.31,
        metric="brier",
        status="comprovada",
        notes="reexecutado com atestado válido",
        path=registro,
        pipeline_fingerprint=rec["pipeline_fingerprint"],
    )
    t = load_trials(registro)[0]
    assert t["status"] == "comprovada"
    assert t["sharpe"] == 0.31
    assert len(t["superseded"]) == 1
    anterior = t["superseded"][0]
    assert anterior["status"] == "refutada"
    assert anterior["sharpe"] == 0.07
    assert anterior["superseded_at"].endswith("Z")
    assert validate_trials(load_trials(registro)) == []


def test_o_historico_e_append_only(registro, tmp_path):
    """Dois flips deixam dois registros — o segundo não apaga o primeiro."""
    rec = _atesta(registro, tmp_path)
    comum = {
        "params": {"h": 7},
        "metric": "brier",
        "path": registro,
        "pipeline_fingerprint": rec["pipeline_fingerprint"],
    }
    register_trial("t-refutada", sharpe=0.31, status="comprovada", **comum)
    register_trial("t-refutada", sharpe=0.12, status="inconclusiva", **comum)

    t = load_trials(registro)[0]
    assert t["status"] == "inconclusiva"
    assert [h["status"] for h in t["superseded"]] == ["refutada", "comprovada"]
    assert validate_trials(load_trials(registro)) == []


def test_atestado_expirado_nao_autoriza_flip(registro, tmp_path):
    """A mesma validade que protege a criação protege a mudança."""
    import json

    _atesta(registro, tmp_path)
    att = attestation_path_for(registro)
    rec = json.loads(att.read_text(encoding="utf-8"))
    rec["expires_at"] = "2020-01-01T00:00:00Z"
    att.write_text(json.dumps(rec), encoding="utf-8")

    with pytest.raises(PowerAttestationMissingError, match="expirado"):
        register_trial(
            "t-refutada",
            params={"h": 7},
            sharpe=0.31,
            metric="brier",
            status="comprovada",
            path=registro,
            pipeline_fingerprint=rec["pipeline_fingerprint"],
        )
    assert load_trials(registro)[0]["status"] == "refutada"
