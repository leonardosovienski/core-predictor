from pathlib import Path

import pytest
import sync_core


def _legacy_workspace(tmp_path: Path) -> Path:
    package = tmp_path / "consumer" / "vendor" / "predictor_core"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("OLD = True\n", encoding="utf-8")
    return package


def test_audit_is_read_only(tmp_path, monkeypatch):
    vendor = _legacy_workspace(tmp_path)
    before = (vendor / "__init__.py").read_bytes()
    monkeypatch.setattr(sync_core, "PACKAGE_ROOT", vendor)
    assert sync_core.audit(tmp_path) == 0
    assert (vendor / "__init__.py").read_bytes() == before


def test_audit_reports_drift_without_writing(tmp_path, capsys):
    vendor = _legacy_workspace(tmp_path)
    assert sync_core.audit(tmp_path) == 1
    assert "DRIFT" in capsys.readouterr().out
    assert (vendor / "__init__.py").read_text(encoding="utf-8") == "OLD = True\n"


def test_write_is_permanently_rejected():
    with pytest.raises(SystemExit):
        sync_core.main(["--write"])


def test_no_legacy_vendor_is_success(tmp_path, capsys):
    assert sync_core.audit(tmp_path) == 0
    assert "No legacy" in capsys.readouterr().out
