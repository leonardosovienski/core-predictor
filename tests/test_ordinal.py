"""measurement.ordinal — Plackett-Luce: prob soma 1, MLE recupera ordem de força conhecida."""
import pytest

from predictor_core.measurement.ordinal import fit_plackett_luce, plackett_luce_prob, rank_probabilities


def test_plackett_luce_prob_basic():
    strengths = {"a": 3.0, "b": 1.0}
    p_ab = plackett_luce_prob(["a", "b"], strengths)
    p_ba = plackett_luce_prob(["b", "a"], strengths)
    assert p_ab == pytest.approx(0.75)
    assert p_ab + p_ba == pytest.approx(1.0)


def test_plackett_luce_prob_rejects_nonpositive_strength():
    with pytest.raises(ValueError):
        plackett_luce_prob(["a", "b"], {"a": 0.0, "b": 1.0})


def test_rank_probabilities_normalizes():
    probs = rank_probabilities({"a": 3.0, "b": 1.0})
    assert sum(probs.values()) == pytest.approx(1.0)
    assert probs["a"] > probs["b"]


def test_fit_plackett_luce_recovers_dominant_item():
    # "a" sempre vence, "c" sempre perde — MLE deve refletir essa ordem de força.
    rankings = [["a", "b", "c"]] * 20 + [["a", "c", "b"]] * 5
    w = fit_plackett_luce(rankings)
    assert w["a"] > w["b"] > w["c"]


def test_fit_plackett_luce_requires_two_items():
    with pytest.raises(ValueError):
        fit_plackett_luce([["only"]])


def test_fit_plackett_luce_nunca_vencedor_mantem_contrato_w_positivo():
    """Regressão: item sempre-último recebia força 0.0 e plackett_luce_prob
    rejeitava a saída do próprio fit (contrato w>0 violado)."""
    w = fit_plackett_luce([["a", "b", "z"], ["b", "a", "z"], ["a", "b", "z"]])
    assert all(v > 0 for v in w.values())
    assert w["z"] < w["a"] and w["z"] < w["b"]
    assert plackett_luce_prob(["a", "b", "z"], w) > 0  # aceita a própria saída
