import subprocess
import sys


def test_root_import_does_not_load_optional_infrastructure():
    code = """
import sys
import predictor_core
assert "predictor_core.kernel.net" not in sys.modules
assert "predictor_core.measurement.trials" not in sys.modules
from predictor_core import LatencySLA
assert LatencySLA(1, 2).p99_seconds == 2
assert "predictor_core.kernel.net" not in sys.modules
assert "predictor_core.measurement.trials" not in sys.modules
"""
    subprocess.run([sys.executable, "-I", "-c", code], check=True)


def test_all_legacy_exports_still_resolve():
    import predictor_core

    for name in predictor_core.__all__:
        assert getattr(predictor_core, name) is not None

    from predictor_core import contracts

    for name in contracts.__all__:
        assert getattr(contracts, name) is not None
