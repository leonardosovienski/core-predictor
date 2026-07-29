"""contracts/ — a fachada canônica reexporta as MESMAS classes das implementações físicas."""
from predictor_core import contracts
from predictor_core.contracts.points import MarketDataPoint, PredictionPoint
from predictor_core.contracts.registry import TrialRegistry, MetricMismatchError
from predictor_core.data.contracts import MarketDataPoint as PhysicalMDP, PredictionPoint as PhysicalPP
from predictor_core.measurement.trials import TrialRegistry as PhysicalTR, MetricMismatchError as PhysicalMME


def test_points_facade_is_same_object():
    assert MarketDataPoint is PhysicalMDP
    assert PredictionPoint is PhysicalPP


def test_registry_facade_is_same_object():
    assert TrialRegistry is PhysicalTR
    assert MetricMismatchError is PhysicalMME


def test_package_facade_exports():
    assert contracts.PredictionPoint is PhysicalPP
    assert contracts.TrialRegistry is PhysicalTR
