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


def test_emit_event_rejeita_metric_nao_finita(tmp_path):
    """Regressão: NaN em metrics era serializado como literal fora do RFC 8259 —
    a linha inteira da telemetria virava lixo para parsers estritos."""
    with pytest.raises(ValueError, match="não-finito"):
        obs.emit_event("d", "e", metrics={"psr": float("nan")}, path=tmp_path / "e.jsonl")
    with pytest.raises(ValueError):
        obs.emit_event("d", "e", metrics={"x": float("inf")}, path=tmp_path / "e.jsonl")
    assert not (tmp_path / "e.jsonl").exists()  # nada gravado


def test_emit_event_rejeita_nan_escondido_no_metadata(tmp_path):
    with pytest.raises(ValueError):
        obs.emit_event("d", "e", metadata={"raw": float("nan")}, path=tmp_path / "e.jsonl")


def test_read_events_reports_line_context_on_truncated_jsonl(tmp_path):
    # Regressão: uma linha truncada no fim do arquivo (crash a meio da escrita)
    # derrubava a leitura inteira com um json.JSONDecodeError cru, sem dizer
    # qual arquivo/linha — mesma filosofia de kernel.jsonl_store.JsonlStore
    # (falha barulhenta, mas com contexto acionável).
    p = tmp_path / "events.jsonl"
    p.write_text(
        '{"a": 1}\n{"a": 2}\n{"a": 3, "trunc', encoding="utf-8")
    with pytest.raises(ValueError, match=r"events\.jsonl:3"):
        obs.read_events(p)
