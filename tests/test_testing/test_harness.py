"""harness — controle positivo: um veredito só vale se o pipeline tem poder."""
import pytest

from predictor_core.measurement.bootstrap import bootstrap_ci
from predictor_core.testing.harness import assert_pipeline_has_power, PipelineHasNoPowerError
from predictor_core.testing.synth import ar1_series


def _mean(u):
    return sum(u) / len(u)


def _good_pipeline(series):
    """Pipeline honesto usando a régua do core: COMPROVADA se o IC 95% da média
    exclui zero por baixo (lo > 0); senão REFUTADA."""
    lo, hi, _ = bootstrap_ci(series, _mean, scheme="iid", n_boot=500, seed=1)
    return {"verdict": "COMPROVADA" if (lo is not None and lo > 0) else "REFUTADA"}


def _edge_gen():
    # média verdadeira +0.03, ruído pequeno → IC bem acima de zero → detectável
    return ar1_series(200, 0.0, 0.02, seed=1, mu=0.03)


def _noise_gen():
    # média verdadeira 0 → IC contém zero → deve ser rejeitado
    return ar1_series(200, 0.0, 0.02, seed=2, mu=0.0)


def test_harness_positive():
    """Pipeline honesto detecta edge E rejeita ruído → controle positivo passa."""
    assert assert_pipeline_has_power(_good_pipeline, _edge_gen, _noise_gen) is True


def test_harness_catches_blind_pipeline():
    """Pipeline que NUNCA confirma (sempre REFUTADA) falha a SENSIBILIDADE."""
    blind = lambda s: {"verdict": "REFUTADA"}
    with pytest.raises(PipelineHasNoPowerError):
        assert_pipeline_has_power(blind, _edge_gen, _noise_gen)


def test_harness_catches_credulous_pipeline():
    """Pipeline que SEMPRE confirma (sempre COMPROVADA) falha a ESPECIFICIDADE
    (confirma ruído) — fabrica significância."""
    credulous = lambda s: {"verdict": "COMPROVADA"}
    with pytest.raises(PipelineHasNoPowerError):
        assert_pipeline_has_power(credulous, _edge_gen, _noise_gen)
