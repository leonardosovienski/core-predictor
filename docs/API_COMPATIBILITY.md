# API compatibility report

## Result

The 2.1.0 packaging migration preserves the public `predictor_core` facade and all
canonical submodule paths. It changes distribution and removes only accidental
checkout-dependent imports.

| Surface before migration | Result | Guarantee |
|---|---|---|
| `import predictor_core` and root `__all__` | Preserved | Snapshot-tested |
| `predictor_core.kernel.*` | Preserved | Existing suite |
| `predictor_core.measurement.*` | Preserved | Existing and golden suite |
| `predictor_core.data.*` | Preserved | Existing anti-lookahead tests |
| `predictor_core.contracts.*` | Preserved | Facade identity tests |
| `predictor_core.testing.*` | Preserved | Existing suite |
| flat `predictor_core.stats`, `.infra`, `.net`, `.obs`, `.replay`, `.settings` | Preserved temporarily | Import-tested compatibility shims |
| bare `import stats` / checkout named `predictor_core` | Removed | Accidental, depended on checkout/PYTHONPATH |

The contracts remain inside this distribution because they are thin identity facades
over implementation types. A separate package would duplicate ownership/versioning
without reducing the core's zero-dependency runtime; separation is therefore not
beneficial at this time.

Numerical behavior is locked by deterministic seeds and explicit `pytest.approx`
tolerances. No model, feature, threshold, population, trial, ledger, gate, or capital
state was changed by this migration.
