"""sync_core --check deve re-hashear os BYTES do vendor, não confiar no manifest.

O cenário que a salvaguarda existe para pegar: alguém "conserta" a matemática
dentro de um domínio (edita vendor/predictor_core/*.py) sem tocar no
CORE_MANIFEST.json. Um check que só compara o agregado GRAVADO no manifest
diria "em sincronia" — adulteração invisível.
"""
import sync_core


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
