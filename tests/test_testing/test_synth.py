"""synth — geradores sintéticos: determinismo e verdade conhecida."""
from predictor_core.testing.synth import ar1_series, edge_injected, probabilistic_predictor


def test_ar1_deterministic_by_seed():
    a = ar1_series(50, 0.5, 1.0, seed=3)
    b = ar1_series(50, 0.5, 1.0, seed=3)
    c = ar1_series(50, 0.5, 1.0, seed=4)
    assert a == b                    # mesma seed → série idêntica
    assert a != c                    # seed diferente → série diferente
    assert len(a) == 50


def test_ar1_iid_when_phi_zero():
    # phi=0 → ruído i.i.d. em torno de mu; média amostral perto de mu
    s = ar1_series(2000, 0.0, 1.0, seed=1, mu=0.5)
    assert abs(sum(s) / len(s) - 0.5) < 0.1


def test_edge_injected_shifts_mean_by_known_amount():
    base = ar1_series(100, 0.0, 1.0, seed=2, mu=0.0)
    bumped = edge_injected(base, 0.3)          # todas as posições
    diff = sum(bumped) / len(bumped) - sum(base) / len(base)
    assert abs(diff - 0.3) < 1e-9
    assert base is not bumped                   # não muta o original


def test_edge_injected_specific_positions():
    base = [0.0] * 10
    out = edge_injected(base, 1.0, positions=[0, 5, 9])
    assert out[0] == 1.0 and out[5] == 1.0 and out[9] == 1.0
    assert out[1] == 0.0 and sum(out) == 3.0


def test_probabilistic_predictor_skill_extremes():
    probs0, out0 = probabilistic_predictor(50, skill_level=0.0, seed=1, n_classes=3)
    probs1, out1 = probabilistic_predictor(50, skill_level=1.0, seed=1, n_classes=3)
    # skill 0 → uniforme (1/3 em cada classe)
    assert all(abs(p[j] - 1 / 3) < 1e-9 for p in probs0 for j in range(3))
    # skill 1 → one-hot na classe verdadeira
    assert all(probs1[i][out1[i]] == 1.0 for i in range(50))


def test_probabilistic_predictor_deterministic():
    a = probabilistic_predictor(30, 0.5, seed=7)
    b = probabilistic_predictor(30, 0.5, seed=7)
    assert a == b
