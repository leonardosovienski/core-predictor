"""Compact scientific golden vector; changes require separate scientific review."""

from datetime import UTC, datetime

import pytest

from predictor_core.data.contracts import PredictionPoint
from predictor_core.kernel.rating import expected_score, update_pair
from predictor_core.measurement.bootstrap import bootstrap_ci
from predictor_core.measurement.calibration import PlattCalibrator
from predictor_core.measurement.metrics import brier, log_loss, rps
from predictor_core.measurement.ordinal import plackett_luce_prob
from predictor_core.measurement.replay import LookaheadError, replay
from predictor_core.measurement.trials import load_trials, register_trial, validate_trials

REL = 1e-12
ABS = 1e-12


def test_metrics_bootstrap_calibration_elo_and_ordinal_golden():
    probs = [[0.8, 0.2], [0.3, 0.7]]
    assert brier(probs, [0, 1]) == pytest.approx(0.13, rel=REL, abs=ABS)
    assert log_loss(probs, [0, 1]) == pytest.approx(0.2899092476264711, rel=REL, abs=ABS)
    assert rps([[0.7, 0.2, 0.1], [0.1, 0.3, 0.6]], [0, 2]) == pytest.approx(
        0.0675, rel=REL, abs=ABS
    )
    lo, hi, _ = bootstrap_ci(
        [1.0, 2.0, 3.0, 4.0, 5.0],
        lambda xs: sum(xs) / len(xs),
        scheme="iid",
        n_boot=200,
        seed=17,
    )
    assert (lo, hi) == pytest.approx((2.0, 4.2), rel=REL, abs=ABS)
    calibrated = (
        PlattCalibrator(iterations=100)
        .fit([0.2, 0.4, 0.6, 0.8], [0, 0, 1, 1])
        .transform([0.25, 0.75])
    )
    assert calibrated == pytest.approx([0.07423505854562747, 0.9257649414543724], rel=REL, abs=ABS)
    assert expected_score(1600, 1500) == pytest.approx(0.6400649998028851, rel=REL, abs=ABS)
    assert update_pair(1600, 1500, 1, k=32) == pytest.approx(
        (1611.5179200063076, 1488.4820799936924), rel=REL, abs=ABS
    )
    assert plackett_luce_prob(["a", "b"], {"a": 3.0, "b": 1.0}) == pytest.approx(
        0.75, rel=REL, abs=ABS
    )


def test_anti_lookahead_and_experiment_registry_golden(tmp_path):
    with pytest.raises(LookaheadError):
        replay([1, 2], lambda past: past[past.asof_index + 1])
    predicted = datetime(2026, 8, 1, tzinfo=UTC)
    with pytest.raises(ValueError):
        PredictionPoint(predicted, datetime(2026, 7, 31, tzinfo=UTC), 0.5, {})

    registry = tmp_path / "trials.json"
    register_trial(
        "golden-v1",
        params={"window": 7},
        sharpe=0.25,
        path=registry,
        now="2026-08-01T00:00:00Z",
        power_attestation=False,
    )
    records = load_trials(registry)
    assert validate_trials(records) == []
    assert records == [
        {
            "name": "golden-v1",
            "registered_at": "2026-08-01T00:00:00Z",
            "params": {"window": 7},
            "sharpe": 0.25,
            "notes": "",
        }
    ]
