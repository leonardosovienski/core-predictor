"""Functional distribution gate. Run with the wheel's Python using -I, outside source."""

import argparse
import hashlib
import importlib.metadata
import json
import math
import subprocess
import sys
import tempfile
import unittest
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import predictor_core
from predictor_core import obs, settings
from predictor_core.contracts.scientific import LatencySLA, ResourceBudget
from predictor_core.data.contracts import PredictionPoint
from predictor_core.measurement.bootstrap import bootstrap_ci
from predictor_core.measurement.metrics import brier, log_loss
from predictor_core.measurement.replay import LookaheadError, replay


def identity(wheel):
    digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
    dist = importlib.metadata.distribution("predictor-core")
    direct = json.loads(dist.read_text("direct_url.json") or "{}")
    recorded = direct.get("archive_info", {}).get("hashes", {}).get("sha256")
    if recorded is not None and recorded != digest:
        raise RuntimeError("Installed archive hash differs from the supplied wheel")
    # uv may omit archive hashes for local wheels. Check every package byte too.
    with zipfile.ZipFile(wheel) as archive:
        for member in archive.namelist():
            if member.startswith("predictor_core/") and not member.endswith("/"):
                installed = Path(dist.locate_file(member))
                if installed.read_bytes() != archive.read(member):
                    raise RuntimeError(f"Installed content differs from wheel: {member}")
    if dist.version != predictor_core.__version__:
        raise RuntimeError("Distribution and module versions differ")
    prefix = Path(sys.prefix).resolve()
    for name, module in tuple(sys.modules.items()):
        if name == "predictor_core" or name.startswith("predictor_core."):
            path = Path(module.__file__).resolve()
            if not path.is_relative_to(prefix):
                raise RuntimeError(f"Source contamination: {name}: {path}")
    return dict(version=dist.version, module=predictor_core.__file__, sha256=digest)


class InstalledBehavior(unittest.TestCase):
    def test_metrics_independent_formula(self):
        probabilities = [[0.8, 0.2], [0.3, 0.7]]
        self.assertAlmostEqual(brier(probabilities, [0, 1]), 0.13, places=12)
        expected = -(math.log(0.8) + math.log(0.7)) / 2
        self.assertAlmostEqual(log_loss(probabilities, [0, 1]), expected, places=12)

    def test_bootstrap_constant_and_seed(self):
        mean = lambda xs: sum(xs) / len(xs)
        result = bootstrap_ci([2.0] * 5, mean, scheme="iid", n_boot=100, seed=17)
        self.assertEqual(result[:2], (2.0, 2.0))
        args = dict(scheme="iid", n_boot=100, seed=17)
        self.assertEqual(
            bootstrap_ci([1, 2, 3], mean, **args), bootstrap_ci([1, 2, 3], mean, **args)
        )

    def test_replay_visibility_order_and_availability(self):
        self.assertEqual(replay([1, 2, 3], lambda past: tuple(past[:])), [(1,), (1, 2), (1, 2, 3)])
        with self.assertRaises(LookaheadError):
            replay([1, 2], lambda past: past[past.asof_index + 1])
        with self.assertRaises(ValueError):
            replay([2, 1], lambda past: None, key=lambda value: value)
        called = []
        with self.assertRaises(LookaheadError):
            replay(
                [(1, 2)],
                lambda past: called.append(past),
                key=lambda event: event[0],
                available_at=lambda event: event[1],
            )
        self.assertEqual(called, [])

    def test_temporal_contract(self):
        with self.assertRaises(ValueError):
            PredictionPoint(
                datetime(2026, 8, 1, tzinfo=UTC), datetime(2026, 7, 31, tzinfo=UTC), 0.5, {}
            )

    def test_nonfinite_contracts(self):
        for contract in (LatencySLA, ResourceBudget):
            for value in (float("nan"), float("inf"), -float("inf")):
                for values in ((value, 2), (1, value)):
                    with self.subTest(contract=contract, values=values):
                        with self.assertRaises(ValueError):
                            contract(*values)

    def test_compatibility_settings_behavior(self):
        env = {"TEST_KEY": "synthetic-functional-test-value"}
        self.assertEqual(settings.require_secrets("TEST_KEY", env=env), env)
        with self.assertRaises(settings.MissingCredentialsError):
            settings.require_secrets("TEST_KEY", env={"TEST_KEY": "dummy"})

    def test_compatibility_observation_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            record = obs.emit_event(
                "fixture",
                "measurement",
                metrics={"brier": 0.13},
                path=path,
                timestamp="2026-08-01T00:00:00+00:00",
            )
            self.assertEqual(obs.read_events(path), [record])
            before = path.read_bytes()
            with self.assertRaises(ValueError):
                obs.emit_event("fixture", "invalid", metrics={"x": float("nan")}, path=path)
            self.assertEqual(path.read_bytes(), before)

    def test_root_import_has_no_io_or_optional_import(self):
        code = """
import sys
def guard(event, args):
    if event.startswith("socket.") or event in ("os.mkdir", "subprocess.Popen"):
        raise RuntimeError(event)
    if event == "open" and isinstance(args[1], str) and any(c in args[1] for c in "wax+"):
        raise RuntimeError("write during import")
sys.addaudithook(guard)
import predictor_core
assert "predictor_core.kernel.net" not in sys.modules
assert "predictor_core.measurement.trials" not in sys.modules
assert predictor_core.LatencySLA(1, 2).p99_seconds == 2
"""
        subprocess.run([sys.executable, "-I", "-B", "-c", code], check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path, required=True)
    args = parser.parse_args()
    if not sys.flags.isolated:
        raise SystemExit("Use Python -I")
    print(json.dumps(identity(args.wheel)), flush=True)
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(InstalledBehavior)
    )
    print(json.dumps(identity(args.wheel)), flush=True)
    raise SystemExit(not result.wasSuccessful())
