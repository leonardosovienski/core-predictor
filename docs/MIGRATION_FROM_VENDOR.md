# Migration from `vendor/predictor_core`

1. Record `runtime_core_version`, `vendored_core_version` (or `NOT_PRESENT`) and the
   result of the consumer's compatibility/golden check. Never infer runtime version
   from a checked-in vendor directory.
2. Pin the released wheel in the consumer manifest: `uv add predictor-core==3.1.0`
   (add `--extra http` and/or `--extra scraping` when those capabilities are used).
3. Replace any path injection or sibling-repository import with normal
   `predictor_core` imports. Existing `predictor_core.*` imports remain valid.
4. Run the consumer's scientific golden suite against the installed wheel. Treat a
   mismatch between runtime and vendor as drift, not as evidence about runtime code.
5. Remove `vendor/predictor_core`, `CORE_MANIFEST.json`, sync jobs, and `PYTHONPATH`.
6. Verify from outside both checkouts with `python -I -c "import predictor_core"`.

Rollback is a dependency-pin change to the previously released wheel; do not restore
cross-repository synchronization. `python sync_core.py --audit` only reports remaining
legacy copies and never modifies a consumer.
