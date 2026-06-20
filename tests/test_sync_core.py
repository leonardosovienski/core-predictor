import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from predictor_core.sync_core import (
    CANONICAL,
    MANIFEST_NAME,
    _sha256,
    cmd_check,
    cmd_write,
    consumers,
    manifest,
    payload_files,
)


def test_payload_files_include_python_and_version(tmp_path):
    (tmp_path / "a.py").write_text("print('a')", encoding="utf-8")
    (tmp_path / "b.py").write_text("print('b')", encoding="utf-8")
    (tmp_path / "VERSION").write_text("0.0.1", encoding="utf-8")
    (tmp_path / "sync_core.py").write_text("", encoding="utf-8")
    (tmp_path / MANIFEST_NAME).write_text("{}", encoding="utf-8")

    files = payload_files(tmp_path)
    assert sorted(p.name for p in files) == ["VERSION", "a.py", "b.py"]


def test_manifest_contains_aggregate(tmp_path):
    p = tmp_path / "a.py"
    p.write_text("foo", encoding="utf-8")

    m = manifest(tmp_path)
    assert "files" in m
    assert "aggregate" in m
    assert m["files"]["a.py"] == _sha256(p)


def test_cmd_check_reports_drift(monkeypatch, tmp_path, capsys):
    root = tmp_path / "workspace"
    core = root / "predictor_core"
    core.mkdir(parents=True)
    (core / "a.py").write_text("foo", encoding="utf-8")
    (core / "VERSION").write_text("0.0.1", encoding="utf-8")

    consumer = root / "consumer"
    vendor = consumer / "vendor" / "predictor_core"
    vendor.mkdir(parents=True)
    (vendor / MANIFEST_NAME).write_text(json.dumps({"aggregate": "deadbeef"}), encoding="utf-8")

    monkeypatch.setattr("predictor_core.sync_core.WORKSPACE", root)
    monkeypatch.setattr("predictor_core.sync_core.CANONICAL", core)

    rc = cmd_check()
    captured = capsys.readouterr()
    assert rc == 1
    assert "DRIFT" in captured.out


def test_cmd_write_syncs_vendor_and_prunes_stale_files(monkeypatch, tmp_path):
    root = tmp_path / "workspace"
    core = root / "predictor_core"
    core.mkdir(parents=True)
    (core / "a.py").write_text("foo", encoding="utf-8")
    (core / "b.py").write_text("bar", encoding="utf-8")
    (core / "VERSION").write_text("0.0.1", encoding="utf-8")

    consumer = root / "consumer"
    vendor = consumer / "vendor" / "predictor_core"
    vendor.mkdir(parents=True)
    (vendor / "stale.py").write_text("stale", encoding="utf-8")

    monkeypatch.setattr("predictor_core.sync_core.WORKSPACE", root)
    monkeypatch.setattr("predictor_core.sync_core.CANONICAL", core)

    rc = cmd_write()
    assert rc == 0
    assert (vendor / MANIFEST_NAME).exists()
    manifest_data = json.loads((vendor / MANIFEST_NAME).read_text(encoding="utf-8"))
    assert manifest_data["aggregate"] == manifest(core)["aggregate"]
    assert not (vendor / "stale.py").exists()


def test_consumers_finds_vendor_consumers(tmp_path, monkeypatch):
    root = tmp_path / "workspace"
    core = root / "predictor_core"
    core.mkdir(parents=True)
    consumer = root / "consumer"
    vendor = consumer / "vendor" / "predictor_core"
    vendor.mkdir(parents=True)

    monkeypatch.setattr("predictor_core.sync_core.WORKSPACE", root)
    monkeypatch.setattr("predictor_core.sync_core.CANONICAL", core)

    found = consumers()
    assert found == [consumer]
