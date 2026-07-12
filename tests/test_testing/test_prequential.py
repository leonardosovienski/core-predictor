"""testing.prequential — Template Method: fatiamento sem leakage, target blindado."""
import pytest

from predictor_core.testing.prequential import PrequentialEvaluator


class _MeanEvaluator(PrequentialEvaluator):
    """Prevê a média dos targets do histórico — e GRAVA o que recebeu, para
    os testes inspecionarem as garantias anti-leakage."""

    def __init__(self):
        super().__init__(target_key="y")
        self.seen_histories = []
        self.seen_features = []

    def train_step(self, history):
        self.seen_histories.append(history)
        ys = [h["y"] for h in history]
        self.mean = sum(ys) / len(ys)

    def predict_step(self, features):
        self.seen_features.append(features)
        return self.mean


def _obs(n):
    return [{"t": i, "y": float(i)} for i in range(n)]


def test_run_pairs_prediction_with_actual():
    ev = _MeanEvaluator()
    results = ev.run(_obs(5), min_history=2)
    assert [r["index"] for r in results] == [2, 3, 4]
    assert results[0]["actual"] == 2.0
    assert results[0]["prediction"] == pytest.approx(0.5)  # média de {0,1}


def test_train_never_sees_future():
    ev = _MeanEvaluator()
    ev.run(_obs(6), min_history=3)
    for i, hist in enumerate(ev.seen_histories):
        assert max(h["t"] for h in hist) < 3 + i  # só passado estrito


def test_predict_never_sees_target():
    ev = _MeanEvaluator()
    ev.run(_obs(5), min_history=2)
    assert all("y" not in f for f in ev.seen_features)
    assert all("t" in f for f in ev.seen_features)


def test_retrain_every_amortizes_training():
    ev = _MeanEvaluator()
    ev.run(_obs(10), min_history=2, retrain_every=4)
    assert len(ev.seen_histories) == 2  # treina em i=2 e i=6
    assert len(ev.seen_features) == 8   # mas prevê todos os passos


def test_missing_target_raises():
    ev = _MeanEvaluator()
    obs = _obs(4)
    del obs[3]["y"]
    with pytest.raises(KeyError):
        ev.run(obs, min_history=2)


def test_invalid_config_raises():
    with pytest.raises(ValueError):
        _MeanEvaluator().run(_obs(5), min_history=0)
    class NoTarget(PrequentialEvaluator):
        def __init__(self):
            super().__init__(target_key="")
        def train_step(self, h): ...
        def predict_step(self, f): ...
    with pytest.raises(ValueError):
        NoTarget()
