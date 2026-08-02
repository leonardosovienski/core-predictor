"""contracts/ — a fachada canônica reexporta as MESMAS classes das implementações físicas."""

from predictor_core import contracts
from predictor_core.contracts.points import MarketDataPoint, PredictionPoint
from predictor_core.contracts.registry import MetricMismatchError, TrialRegistry
from predictor_core.data.contracts import MarketDataPoint as PhysicalMDP
from predictor_core.data.contracts import PredictionPoint as PhysicalPP
from predictor_core.measurement.trials import MetricMismatchError as PhysicalMME
from predictor_core.measurement.trials import TrialRegistry as PhysicalTR


def test_points_facade_is_same_object():
    assert MarketDataPoint is PhysicalMDP
    assert PredictionPoint is PhysicalPP


def test_registry_facade_is_same_object():
    assert TrialRegistry is PhysicalTR
    assert MetricMismatchError is PhysicalMME


def test_package_facade_exports():
    assert contracts.PredictionPoint is PhysicalPP
    assert contracts.TrialRegistry is PhysicalTR
