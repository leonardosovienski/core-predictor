"""O atestado de poder recusa árvore de trabalho suja.

Auditoria adversarial 2026-09-05, achado 7: o atestado em produção do consumidor
trazia `code_version` terminando em `;dirty`. O rótulo era honesto, mas o efeito
é que o código que passou no controle positivo — o controle que DESTRAVA o
registro de trials novas — não é identificável por commit nenhum. O atestado
autorizava trials que ninguém consegue reproduzir.

Estes testes fixam a nova regra: fail-closed por padrão, escape explícito.
"""

from __future__ import annotations

import subprocess

import pytest

from predictor_core.testing.harness import (
    DirtyWorkingTreeError,
    attest_pipeline_power,
)


def _eval_mean(series):
    mean = sum(series) / len(series)
    return {"verdict": "COMPROVADA" if mean > 0.5 else "REFUTADA"}


def _attest(path, repo, **kw):
    return attest_pipeline_power(
        _eval_mean,
        lambda: [1.0] * 10,
        lambda: [0.0] * 10,
        attestation_path=path,
        metric="brier",
        repo=repo,
        **kw,
    )


def _git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


@pytest.fixture
def repo_limpo(tmp_path):
    """Repositório git real com um commit e árvore limpa."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    (repo / "a.txt").write_text("original\n", encoding="utf-8")
    _git(repo, "add", "a.txt")
    _git(repo, "commit", "-qm", "inicial")
    return repo


def test_arvore_suja_recusa_e_nao_grava_nada(tmp_path, repo_limpo):
    """Sujar a árvore basta para bloquear — e nada é escrito em disco."""
    (repo_limpo / "a.txt").write_text("modificado sem commit\n", encoding="utf-8")
    destino = tmp_path / "trials.harness_attestation.json"

    with pytest.raises(DirtyWorkingTreeError, match="árvore de trabalho suja"):
        _attest(destino, repo_limpo)

    assert not destino.exists(), "atestado recusado não pode deixar arquivo para trás"


def test_arvore_limpa_emite_e_grava_code_version(tmp_path, repo_limpo):
    """Com árvore limpa o atestado sai, e agora carrega a proveniência do código."""
    destino = tmp_path / "trials.harness_attestation.json"
    rec = _attest(destino, repo_limpo)

    assert destino.exists()
    assert rec["code_version"].startswith("package:")
    assert ";git:" in rec["code_version"]
    assert not rec["code_version"].endswith(";dirty")


def test_allow_dirty_e_o_unico_escape_e_e_explicito(tmp_path, repo_limpo):
    """O escape existe para exploração local, e fica gravado no próprio atestado."""
    (repo_limpo / "a.txt").write_text("modificado sem commit\n", encoding="utf-8")
    destino = tmp_path / "trials.harness_attestation.json"

    rec = _attest(destino, repo_limpo, allow_dirty=True)

    assert destino.exists()
    assert rec["code_version"].endswith(";dirty"), (
        "quem usa o escape precisa conseguir provar depois que a trial nasceu suja"
    )


def test_arquivo_novo_nao_rastreado_tambem_suja(tmp_path, repo_limpo):
    """`git status --porcelain` conta não-rastreados; a recusa acompanha isso."""
    (repo_limpo / "novo.py").write_text("x = 1\n", encoding="utf-8")
    destino = tmp_path / "trials.harness_attestation.json"

    with pytest.raises(DirtyWorkingTreeError):
        _attest(destino, repo_limpo)

    assert not destino.exists()


def test_fora_de_repositorio_nao_e_tratado_como_sujo(tmp_path):
    """Sem git não há SHA nem estado sujo — o atestado sai, sem alegar commit.

    É o caso de quem consome o core a partir de uma wheel instalada, fora de um
    checkout. Recusar aqui quebraria esse uso sem ganho de proveniência.
    """
    destino = tmp_path / "trials.harness_attestation.json"
    rec = _attest(destino, tmp_path)

    assert destino.exists()
    assert rec["code_version"].startswith("package:")
    assert ";git:" not in rec["code_version"]
