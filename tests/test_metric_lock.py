"""Punição global (v1.3.0): trial com métrica ≠ da atestada é barrada pelo registry."""
import pytest

from predictor_core.measurement.bootstrap import bootstrap_ci
from predictor_core.measurement.trials import MetricMismatchError, register_trial, attestation_path_for
from predictor_core.testing.harness import attest_pipeline_power
from predictor_core.testing.synth import ar1_series


def _pipeline(series):
    lo, _, _ = bootstrap_ci(series, lambda u: sum(u) / len(u), scheme="iid", n_boot=300, seed=1)
    return {"verdict": "COMPROVADA" if (lo is not None and lo > 0) else "REFUTADA"}


def _attest(trials_path, metric):
    return attest_pipeline_power(
        _pipeline,
        lambda: ar1_series(200, 0.0, 0.02, seed=1, mu=0.03),
        lambda: ar1_series(200, 0.0, 0.02, seed=2, mu=0.0),
        attestation_path=attestation_path_for(trials_path), metric=metric)


def test_matching_metric_passes(tmp_path):
    trials = tmp_path / "trials.json"
    att = _attest(trials, metric="brier")
    out = register_trial("t1", params={"m": 1}, path=trials, metric="brier",
                         pipeline_fingerprint=att["pipeline_fingerprint"])
    assert out[0]["metric"] == "brier"


def test_mismatched_metric_is_punished(tmp_path):
    trials = tmp_path / "trials.json"
    att = _attest(trials, metric="brier")
    with pytest.raises(MetricMismatchError):
        register_trial("t1", params={"m": 1}, path=trials, metric="rps",
                       pipeline_fingerprint=att["pipeline_fingerprint"])


def test_metric_omitted_is_rejected_for_new_trial(tmp_path):
    trials = tmp_path / "trials.json"
    att = _attest(trials, metric="brier")
    with pytest.raises(MetricMismatchError):
        register_trial("t1", params={"m": 1}, path=trials,
                       pipeline_fingerprint=att["pipeline_fingerprint"])


def test_attestation_requires_metric(tmp_path):
    trials = tmp_path / "trials.json"
    with pytest.raises(ValueError, match="metric"):
        _attest(trials, metric="")
