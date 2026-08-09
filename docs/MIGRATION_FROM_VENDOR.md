# Migration from `vendor/predictor_core`

1. Pin the released wheel in the consumer manifest: `uv add predictor-core==2.2.0`
   (add `--extra http` and/or `--extra scraping` when those capabilities are used).
2. Replace any path injection or sibling-repository import with normal
   `predictor_core` imports. Existing `predictor_core.*` imports remain valid.
3. Run the consumer's scientific golden suite against the installed wheel.
4. Remove `vendor/predictor_core`, `CORE_MANIFEST.json`, sync jobs, and `PYTHONPATH`.
5. Verify from outside both checkouts with `python -I -c "import predictor_core"`.

Rollback is a dependency-pin change to the previously released wheel; do not restore
cross-repository synchronization. `python sync_core.py --audit` only reports remaining
legacy copies and never modifies a consumer.
