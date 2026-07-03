"""Redireciona a telemetria JSONL para um arquivo temporário durante os testes de data/
(o CircuitBreaker e os routers emitem eventos; sem isso escreveriam ./events.jsonl no cwd)."""
import pytest


@pytest.fixture(autouse=True)
def _events_to_tmp(tmp_path, monkeypatch):
    monkeypatch.setenv("PREDICTOR_EVENTS_PATH", str(tmp_path / "events.jsonl"))
