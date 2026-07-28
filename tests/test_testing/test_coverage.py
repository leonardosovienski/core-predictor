"""coverage — a régua (Lente 2) validada por propriedade mecânica.

Parâmetros travados empiricamente (determinísticos por seed): iid/cluster cobrem ~0.94
em dado i.i.d.; moving/stationary cobrem ~0.96 em dado autocorrelacionado (phi=0.2),
onde o i.i.d. na MESMA série sub-cobre grosseiramente (~0.87). A cobertura de bloco da
média sub-cobre em amostra finita — daí n_points grande nos esquemas de bloco.
"""
from predictor_core.measurement.bootstrap import bootstrap_ci
from predictor_core.testing.coverage import bootstrap_coverage, coverage_in_band


def test_coverage_iid():
    assert coverage_in_band(bootstrap_ci, "iid", n_series=300, n_points=350,
                                   phi=0.0, n_boot=200, seed=0)


def test_coverage_cluster():
    # cluster com unidades singleton degenera no i.i.d. → cobre em dado sem grupo
    assert coverage_in_band(bootstrap_ci, "cluster", n_series=300, n_points=350,
                                   phi=0.0, n_boot=200, seed=0)


def test_coverage_moving():
    assert coverage_in_band(bootstrap_ci, "moving", n_series=120, n_points=800,
                                   phi=0.2, block_length=15, n_boot=200, seed=0)


def test_coverage_stationary():
    assert coverage_in_band(bootstrap_ci, "stationary", n_series=120, n_points=800,
                                   phi=0.2, block_length=15, n_boot=200, seed=0)


def test_coverage_test_has_power():
    """O teste de cobertura DETECTA uma régua incompatível: o bootstrap i.i.d. aplicado
    a dado fortemente autocorrelacionado (phi=0.4) sub-cobre — a cobertura cai bem
    abaixo da banda e test_bootstrap_coverage retorna False. Sem este poder, um 'passou'
    não significaria nada."""
    assert not coverage_in_band(bootstrap_ci, "iid", n_series=160, n_points=300,
                                       phi=0.4, n_boot=200, seed=0)


def test_block_recovers_autocorrelation():
    """Na MESMA série autocorrelacionada, o esquema de bloco cobre substancialmente
    melhor que o i.i.d. — a razão de o cluster/bloco existirem."""
    cov_moving = bootstrap_coverage(bootstrap_ci, "moving", n_series=120, n_points=800,
                                    phi=0.2, block_length=15, n_boot=200, seed=0)
    cov_iid = bootstrap_coverage(bootstrap_ci, "iid", n_series=120, n_points=800,
                                 phi=0.2, block_length=15, n_boot=200, seed=0)
    assert cov_moving > cov_iid + 0.04
