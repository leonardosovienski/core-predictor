"""trials — registro append/update e DSR que desconta pelo nº de tentativas."""
import math

import pytest

from predictor_core.measurement.trials import (
    TrialRegistry, register_trial, load_trials, expected_max_sharpe, deflated_sharpe_ratio,
)

# Retornos com Sharpe por-período MODESTO (~0.14) — PSR sensível, não saturado em 1.0.
# (retornos constantes dariam std=0 → PSR nan; Sharpe alto saturaria o PSR em 1.0.)
_RETURNS = [0.001 + 0.01 * math.sin(i / 2.0) for i in range(150)]


def test_register_and_load(tmp_path):
    p = tmp_path / "trials.json"
    register_trial("v1", params={"h": 7}, sharpe=0.1, path=p, now="2026-07-03T00:00:00Z")
    register_trial("v2", params={"h": 30}, sharpe=0.2, path=p, now="2026-07-03T00:01:00Z")
    trials = load_trials(p)
    assert [t["name"] for t in trials] == ["v1", "v2"]


def test_reregister_same_name_updates_not_appends(tmp_path):
    p = tmp_path / "trials.json"
    register_trial("v1", params={"h": 7}, sharpe=0.1, path=p, now="2026-01-01T00:00:00Z")
    register_trial("v1", params={"h": 7}, sharpe=0.9, path=p, now="2026-02-01T00:00:00Z")
    trials = load_trials(p)
    assert len(trials) == 1
    assert trials[0]["sharpe"] == 0.9                      # valor atualizado
    assert trials[0]["registered_at"] == "2026-01-01T00:00:00Z"   # data original preservada


def test_expected_max_sharpe_grows_with_n():
    e5 = expected_max_sharpe(5, 0.04)
    e50 = expected_max_sharpe(50, 0.04)
    assert expected_max_sharpe(1, 0.04) == 0.0            # 1 tentativa: sem seleção
    assert e50 > e5 > 0.0                                  # mais tentativas → benchmark maior


def test_dsr_decreases_with_more_trials():
    trial_sharpes_few = [0.1, 0.12]
    trial_sharpes_many = [0.1, 0.12, 0.2, -0.1, 0.3, 0.25, -0.2, 0.4]
    dsr_few = deflated_sharpe_ratio(_RETURNS, trial_sharpes_few)
    dsr_many = deflated_sharpe_ratio(_RETURNS, trial_sharpes_many)
    assert dsr_many["sr0"] > dsr_few["sr0"]               # mais tentativas → SR0 maior
    assert dsr_many["dsr"] < dsr_few["dsr"]               # → DSR menor (mais exigente)


def test_registry_facade_deflates_by_registered_trials(tmp_path):
    reg = TrialRegistry(tmp_path / "trials.json")
    for i, s in enumerate([0.1, 0.2, 0.3, -0.1, 0.25]):
        reg.register(f"cfg{i}", params={"i": i}, sharpe=s, now="2026-07-03T00:00:00Z")
    out = reg.deflated_sharpe(_RETURNS)
    assert out["n_trials"] == 5 and 0.0 <= out["dsr"] <= 1.0
