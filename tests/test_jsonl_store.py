"""kernel.jsonl_store — append-only, streaming, corrupção explícita."""
import pytest

from predictor_core.kernel.jsonl_store import JsonlStore


def test_append_and_iterate(tmp_path):
    store = JsonlStore(tmp_path / "events.jsonl")
    store.append({"kind": "bet", "stake": 10})
    store.append({"kind": "settle", "pnl": -10})
    assert list(store) == [{"kind": "bet", "stake": 10}, {"kind": "settle", "pnl": -10}]


def test_missing_file_iterates_empty(tmp_path):
    assert list(JsonlStore(tmp_path / "nope.jsonl")) == []


def test_count_and_tail(tmp_path):
    store = JsonlStore(tmp_path / "e.jsonl")
    for i in range(5):
        store.append({"i": i})
    assert store.count() == 5
    assert store.tail(2) == [{"i": 3}, {"i": 4}]
    assert store.tail(0) == []


def test_corrupted_line_raises_with_line_number(tmp_path):
    p = tmp_path / "bad.jsonl"
    p.write_text('{"ok": 1}\n{broken\n', encoding="utf-8")
    with pytest.raises(ValueError, match=":2:"):
        list(JsonlStore(p))


def test_unserializable_record_fails_before_write(tmp_path):
    store = JsonlStore(tmp_path / "e.jsonl")
    with pytest.raises(TypeError):
        store.append({"bad": object()})
    assert not store.path.exists()
