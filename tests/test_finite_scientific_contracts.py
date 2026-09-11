import pytest

from predictor_core.contracts.scientific import LatencySLA, ResourceBudget


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
@pytest.mark.parametrize("position", [0, 1])
@pytest.mark.parametrize("contract", [LatencySLA, ResourceBudget])
def test_nonfinite_scientific_scalar_is_rejected(value, position, contract):
    values = [1.0, 2.0]
    values[position] = value
    with pytest.raises(ValueError):
        contract(*values)
