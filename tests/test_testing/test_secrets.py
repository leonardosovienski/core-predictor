"""secrets — o guard pega credencial plantada e passa em texto limpo (controle positivo)."""

import pytest

from predictor_core.testing.secrets import assert_no_secrets_in_events, find_secrets


def test_catches_known_prefixes():
    assert find_secrets("token=sk-ABCDEFGHIJKLMNOPQRSTUVWXYZ012345")  # OpenAI
    assert find_secrets("key AIza" + "B" * 35)  # Gemini
    assert find_secrets("Authorization: Bearer abcdef0123456789abcdef")  # Bearer


def test_clean_text_has_no_hits():
    assert find_secrets('{"score": 0.9, "asset": "bitcoin", "id": "a1b2-c3d4"}') == []


def test_known_value_match_verbatim():
    assert find_secrets("prefix realsecretvalue999 suffix", known_values=["realsecretvalue999"])
    assert find_secrets("nada aqui", known_values=["realsecretvalue999"]) == []


def test_short_known_value_is_ignored():
    # valores curtos não são segredos reais → evita falso-positivo
    assert find_secrets("the cat sat", known_values=["cat"]) == []


def test_absent_file_is_noop(tmp_path):
    assert_no_secrets_in_events(tmp_path / "missing.jsonl")  # não levanta


def test_raises_on_leaked_secret(tmp_path):
    f = tmp_path / "events.jsonl"
    f.write_text(
        '{"metadata": {"resp": "sk-ABCDEFGHIJKLMNOPQRSTUVWXYZ012345"}}\n', encoding="utf-8"
    )
    with pytest.raises(AssertionError):
        assert_no_secrets_in_events(f)
