"""settings — trava P0 de credenciais: crash imediato em chave ausente/falsa/curta.
Funciona com ou sem pydantic instalado (a regra é universal, não pydantic-only)."""
import pytest

import settings


def test_is_fake_secret_catches_bad_values():
    assert settings.is_fake_secret("")               # vazio
    assert settings.is_fake_secret(None)             # ausente
    assert settings.is_fake_secret("changeme")       # placeholder
    assert settings.is_fake_secret("short")          # < 16 chars
    assert not settings.is_fake_secret("uma-chave-real-de-producao-1234")


def test_require_secrets_returns_valid_dict():
    env = {"GEMINI_API_KEY": "chave-real-suficientemente-longa-1",
           "SERP_API_KEY": "outra-chave-real-suficientemente-2"}
    got = settings.require_secrets("GEMINI_API_KEY", "SERP_API_KEY", env=env)
    assert got == env


def test_require_secrets_raises_listing_all_bad():
    env = {"GOOD_KEY": "chave-real-suficientemente-longa-1",
           "EMPTY": "", "PLACEHOLDER": "dummy"}
    with pytest.raises(settings.MissingCredentialsError) as exc:
        settings.require_secrets("GOOD_KEY", "EMPTY", "PLACEHOLDER", env=env)
    msg = str(exc.value)
    assert "EMPTY" in msg and "PLACEHOLDER" in msg and "GOOD_KEY" not in msg
