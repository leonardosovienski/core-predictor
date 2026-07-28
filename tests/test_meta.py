"""meta — fingerprint de artefato: contrato que falha explícito na incompatibilidade."""
import warnings

import pytest

from predictor_core.kernel.meta import fingerprint, validate, StaleModelError


def test_fingerprint_deterministic():
    a = fingerprint(1, ("x", "y"), {"alpha": 0.1})
    b = fingerprint(1, ("x", "y"), {"alpha": 0.1})
    assert a == b
    assert a["schema_version"] == 1 and a["features"] == ["x", "y"]


def test_fingerprint_feature_order_matters():
    # ordem das features = ordem das colunas: trocar a ordem é outro contrato
    assert fingerprint(1, ("x", "y"), {}) != fingerprint(1, ("y", "x"), {})


def test_fingerprint_params_change_detected():
    assert fingerprint(1, ("x",), {"a": 1}) != fingerprint(1, ("x",), {"a": 2})


def test_validate_ok_when_equal():
    fp = fingerprint(2, ("a", "b"), {"k": 3})
    assert validate(fp, fp) is None   # não levanta


def test_validate_raises_on_mismatch():
    saved = fingerprint(1, ("a",), {})
    current = fingerprint(2, ("a",), {})   # schema mudou
    with pytest.raises(StaleModelError):
        validate(saved, current)


def test_validate_warns_on_legacy_none():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        validate(None, fingerprint(1, ("a",), {}))
    assert any(issubclass(x.category, RuntimeWarning) for x in w)
