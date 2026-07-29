"""sync_core --check deve re-hashear os BYTES do vendor, não confiar no manifest.

O cenário que a salvaguarda existe para pegar: alguém "conserta" a matemática
dentro de um domínio (edita vendor/predictor_core/*.py) sem tocar no
CORE_MANIFEST.json. Um check que só compara o agregado GRAVADO no manifest
diria "em sincronia" — adulteração invisível.
"""
import json

import pytest

import sync_core

# Auditoria hostil 2026-07-17 (rodada "tools/"): PARKED ficou vazio entre 2026-07-03
# e esta correção — `--write` sem `--target` sincronizou os 3 projetos históricos
# protegidos (wc-predictor-v2, predictor-stocks, nba-predictor) junto dos ativos.
# Este teste fixa a garantia: os 3 nomes reais precisam estar em PARKED.
_PROTEGIDOS = {"wc-predictor-v2", "predictor-stocks", "nba-predictor"}


def _make_workspace(tmp_path):
    """Workspace mínimo: canônico com 1 módulo + VERSION, e 1 consumidor opt-in."""
    canonical = tmp_path / "predictor_core"
    canonical.mkdir()
    (canonical / "mod.py").write_text("X = 1\n", encoding="utf-8")
    (canonical / "VERSION").write_text("9.9.9-test\n", encoding="utf-8")
    vendor = tmp_path / "consumidor" / "vendor" / "predictor_core"
    vendor.mkdir(parents=True)
    return canonical, vendor


def _patch(monkeypatch, canonical):
    monkeypatch.setattr(sync_core, "CANONICAL", canonical)
    monkeypatch.setattr(sync_core, "WORKSPACE", canonical.parent)


def test_write_then_check_em_sincronia(tmp_path, monkeypatch, capsys):
    canonical, vendor = _make_workspace(tmp_path)
    _patch(monkeypatch, canonical)
    assert sync_core.cmd_write() == 0
    assert sync_core.cmd_check() == 0
    assert "OK (em sincronia)" in capsys.readouterr().out


def test_check_detecta_vendor_adulterado_sem_tocar_manifest(tmp_path, monkeypatch, capsys):
    canonical, vendor = _make_workspace(tmp_path)
    _patch(monkeypatch, canonical)
    sync_core.cmd_write()
    # adultera o .py do vendor SEM tocar no CORE_MANIFEST.json
    (vendor / "mod.py").write_text("X = 2  # mascarado\n", encoding="utf-8")
    assert sync_core.cmd_check() == 1
    out = capsys.readouterr().out
    assert "ADULTERADO" in out
    assert "difere:   mod.py" in out


def test_check_detecta_arquivo_orfao_no_vendor(tmp_path, monkeypatch, capsys):
    canonical, vendor = _make_workspace(tmp_path)
    _patch(monkeypatch, canonical)
    sync_core.cmd_write()
    (vendor / "custom.py").write_text("# codigo customizado no vendor\n", encoding="utf-8")
    assert sync_core.cmd_check() == 1
    assert "orfao:    custom.py" in capsys.readouterr().out


def test_check_detecta_drift_de_versao_antiga(tmp_path, monkeypatch, capsys):
    canonical, vendor = _make_workspace(tmp_path)
    _patch(monkeypatch, canonical)
    sync_core.cmd_write()
    # o CANÔNICO evolui; vendor (e manifest dele) ficam para trás
    (canonical / "mod.py").write_text("X = 3\n", encoding="utf-8")
    assert sync_core.cmd_check() == 1
    assert "DRIFT" in capsys.readouterr().out


def test_check_vendor_legado_sem_manifest_mas_em_sincronia(tmp_path, monkeypatch, capsys):
    canonical, vendor = _make_workspace(tmp_path)
    _patch(monkeypatch, canonical)
    sync_core.cmd_write()
    (vendor / sync_core.MANIFEST_NAME).unlink()
    # conteúdo confere byte a byte: não reprova, só orienta a regravar o manifest
    assert sync_core.cmd_check() == 0
    assert "sem manifest" in capsys.readouterr().out


def _make_two_consumer_workspace(tmp_path):
    """Canônico + dois consumidores opt-in (`alvo` e `outro`), ambos já
    sincronizados numa versão antiga do core — usado para provar isolamento
    do sync direcionado."""
    canonical = tmp_path / "predictor_core"
    canonical.mkdir()
    (canonical / "mod.py").write_text("X = 1\n", encoding="utf-8")
    (canonical / "VERSION").write_text("9.9.9-test\n", encoding="utf-8")
    alvo = tmp_path / "alvo" / "vendor" / "predictor_core"
    outro = tmp_path / "outro" / "vendor" / "predictor_core"
    alvo.mkdir(parents=True)
    outro.mkdir(parents=True)
    return canonical, alvo, outro


def _snapshot(vendor: "pathlib.Path") -> dict:
    """{caminho_relativo: (bytes, mtime_ns)} de todo o conteúdo do vendor —
    usado para provar que NADA mudou, não só que o stdout parece certo."""
    import hashlib
    out = {}
    for p in sorted(vendor.rglob("*")):
        if p.is_file():
            rel = p.relative_to(vendor).as_posix()
            out[rel] = (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns)
    return out


def test_check_sem_target_continua_verificando_todos(tmp_path, monkeypatch, capsys):
    canonical, alvo, outro = _make_two_consumer_workspace(tmp_path)
    _patch(monkeypatch, canonical)
    sync_core.cmd_write()
    out = capsys.readouterr().out  # descarta saída do write
    assert sync_core.cmd_check() == 0
    out = capsys.readouterr().out
    assert "alvo" in out and "outro" in out


def test_write_sem_target_preserva_comportamento_legado(tmp_path, monkeypatch, capsys):
    canonical, alvo, outro = _make_two_consumer_workspace(tmp_path)
    _patch(monkeypatch, canonical)
    assert sync_core.cmd_write() == 0
    assert (alvo / "mod.py").read_text(encoding="utf-8") == "X = 1\n"
    assert (outro / "mod.py").read_text(encoding="utf-8") == "X = 1\n"


def test_check_com_target_verifica_somente_o_alvo(tmp_path, monkeypatch, capsys):
    canonical, alvo, outro = _make_two_consumer_workspace(tmp_path)
    _patch(monkeypatch, canonical)
    sync_core.cmd_write()
    capsys.readouterr()
    assert sync_core.cmd_check(target="alvo") == 0
    out = capsys.readouterr().out
    assert "alvo" in out
    assert "outro" not in out


def test_write_com_target_escreve_somente_o_alvo(tmp_path, monkeypatch, capsys):
    canonical, alvo, outro = _make_two_consumer_workspace(tmp_path)
    _patch(monkeypatch, canonical)
    sync_core.cmd_write()  # ambos na versão 1
    (canonical / "mod.py").write_text("X = 2\n", encoding="utf-8")
    (canonical / "VERSION").write_text("9.9.9-test2\n", encoding="utf-8")
    before_outro = _snapshot(outro)
    assert sync_core.cmd_write(target="alvo") == 0
    assert (alvo / "mod.py").read_text(encoding="utf-8") == "X = 2\n"
    assert (outro / "mod.py").read_text(encoding="utf-8") == "X = 1\n"
    assert _snapshot(outro) == before_outro  # byte E timestamp inalterados


def test_nenhum_arquivo_ou_timestamp_de_outros_consumidores_muda(tmp_path, monkeypatch, capsys):
    canonical, alvo, outro = _make_two_consumer_workspace(tmp_path)
    _patch(monkeypatch, canonical)
    sync_core.cmd_write()
    (canonical / "mod.py").write_text("X = 3\n", encoding="utf-8")
    before = _snapshot(outro)
    sync_core.cmd_write(target="alvo")
    sync_core.cmd_check(target="alvo")
    assert _snapshot(outro) == before


def test_target_inexistente_falha_sem_escrita(tmp_path, monkeypatch, capsys):
    canonical, alvo, outro = _make_two_consumer_workspace(tmp_path)
    _patch(monkeypatch, canonical)
    before_alvo, before_outro = _snapshot(alvo), _snapshot(outro)
    assert sync_core.cmd_write(target="nao-existe") == 2
    out = capsys.readouterr().out
    assert "não encontrado" in out
    assert _snapshot(alvo) == before_alvo
    assert _snapshot(outro) == before_outro


def test_target_parcial_nao_e_aceito(tmp_path, monkeypatch, capsys):
    canonical, alvo, outro = _make_two_consumer_workspace(tmp_path)
    _patch(monkeypatch, canonical)
    sync_core.cmd_write()
    before_outro = _snapshot(outro)
    # "alv" é prefixo de "alvo" mas não é o nome exato — deve ser rejeitado
    assert sync_core.cmd_write(target="alv") == 2
    assert _snapshot(outro) == before_outro
    assert not (tmp_path / "alv").exists()


def test_manifest_do_alvo_continua_correto_apos_sync_direcionado(tmp_path, monkeypatch, capsys):
    canonical, alvo, outro = _make_two_consumer_workspace(tmp_path)
    _patch(monkeypatch, canonical)
    sync_core.cmd_write()
    (canonical / "mod.py").write_text("X = 4\n", encoding="utf-8")
    sync_core.cmd_write(target="alvo")
    manifest_alvo = json.loads((alvo / sync_core.MANIFEST_NAME).read_text(encoding="utf-8"))
    assert manifest_alvo["aggregate"] == sync_core.manifest(canonical)["aggregate"]
    assert sync_core.manifest(alvo)["aggregate"] == sync_core.manifest(canonical)["aggregate"]


def test_conteudo_vendorizado_do_alvo_byte_identico_ao_canonico(tmp_path, monkeypatch, capsys):
    canonical, alvo, outro = _make_two_consumer_workspace(tmp_path)
    _patch(monkeypatch, canonical)
    sync_core.cmd_write(target="alvo")
    assert (alvo / "mod.py").read_bytes() == (canonical / "mod.py").read_bytes()
    assert (alvo / "VERSION").read_bytes() == (canonical / "VERSION").read_bytes()


def test_falha_na_preparacao_do_staging_preserva_vendor_anterior(tmp_path, monkeypatch, capsys):
    canonical, vendor = _make_workspace(tmp_path)
    _patch(monkeypatch, canonical)
    sync_core.cmd_write()
    before = _snapshot(vendor)
    (canonical / "mod.py").write_text("X = 2\n", encoding="utf-8")
    original_copy = sync_core.shutil.copy2

    def fail_copy(source, destination, *args, **kwargs):
        if Path(source).name == "mod.py":
            raise OSError("simulated disk failure")
        return original_copy(source, destination, *args, **kwargs)

    from pathlib import Path
    monkeypatch.setattr(sync_core.shutil, "copy2", fail_copy)
    with pytest.raises(OSError, match="simulated disk failure"):
        sync_core.cmd_write()
    assert _snapshot(vendor) == before


def test_resultado_deterministico_exceto_synced_at_do_alvo(tmp_path, monkeypatch, capsys):
    canonical, alvo, outro = _make_two_consumer_workspace(tmp_path)
    _patch(monkeypatch, canonical)
    sync_core.cmd_write(target="alvo")
    m1 = json.loads((alvo / sync_core.MANIFEST_NAME).read_text(encoding="utf-8"))
    sync_core.cmd_write(target="alvo")
    m2 = json.loads((alvo / sync_core.MANIFEST_NAME).read_text(encoding="utf-8"))
    m1.pop("synced_at"), m2.pop("synced_at")
    assert m1 == m2


def test_modo_direcionado_nao_importa_projeto_de_dominio(tmp_path, monkeypatch, capsys):
    # sync_core opera só com Path/hash/JSON — nunca importa o código do
    # consumidor. Confirma que --target não introduz nenhum import novo.
    import inspect
    src = inspect.getsource(sync_core)
    assert "importlib" not in src
    assert "__import__" not in src


def test_parked_contem_os_3_projetos_historicos_protegidos():
    # Regressão (auditoria hostil 2026-07-17): PARKED vazio permitiu que
    # --write sem --target escrevesse vendor/ nos 3 projetos que deveriam
    # estar congelados. Fixa os nomes reais na constante.
    assert sync_core.PARKED == {"wc-predictor-v2", "predictor-stocks", "nba-predictor"}


def test_write_sem_target_pula_projetos_protegidos(tmp_path, monkeypatch, capsys):
    canonical, vendor = _make_workspace(tmp_path)
    _patch(monkeypatch, canonical)
    protegido = tmp_path / "wc-predictor-v2" / "vendor" / "predictor_core"
    protegido.mkdir(parents=True)
    monkeypatch.setattr(sync_core, "PARKED", {"wc-predictor-v2"})
    assert sync_core.cmd_write() == 0
    out = capsys.readouterr().out
    assert "wc-predictor-v2" in out and "PULADO" in out
    assert not (protegido / "mod.py").exists()
    assert not (protegido / sync_core.MANIFEST_NAME).exists()
    assert (vendor / "mod.py").exists()
