"""obs — envelope RÍGIDO de 7 chaves; metrics só numérico; round-trip do JSONL."""
import pytest

import obs


def test_emit_event_writes_full_envelope(tmp_path):
    p = tmp_path / "events.jsonl"
    rec = obs.emit_event("v3_cripto", "wfa_result",
                         metrics={"psr": 0.9}, metadata={"symbol": "BTCUSDT"},
                         path=p, timestamp="2026-06-29T00:00:00+00:00")
    assert tuple(rec.keys()) == obs.ENVELOPE_KEYS         # ordem canônica
    assert rec["run_id"] is None and rec["code_version"] is None  # chave existe mesmo None
    back = obs.read_events(p)
    assert len(back) == 1 and back[0]["event"] == "wfa_result"


def test_emit_event_rejects_non_numeric_metrics(tmp_path):
    with pytest.raises(TypeError):
        obs.emit_event("d", "e", metrics={"status": "ok"}, path=tmp_path / "x.jsonl")


def test_emit_event_requires_domain_and_event(tmp_path):
    with pytest.raises(ValueError):
        obs.emit_event("", "e", path=tmp_path / "x.jsonl")
    with pytest.raises(ValueError):
        obs.emit_event("d", "", path=tmp_path / "x.jsonl")


def test_read_events_missing_file_is_empty(tmp_path):
    assert obs.read_events(tmp_path / "nao_existe.jsonl") == []
