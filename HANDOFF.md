# Handoff

`predictor-core` is now a conventionally packaged scientific library.

- Source: `src/predictor_core/`
- Version source: `project.version` in `pyproject.toml` (`2.2.0`)
- Baseline: Python 3.13; Python 3.14 experimental
- Resolver/build: `uv.lock` and `uv build --wheel`
- Distribution: installed wheel only; vendoring is legacy
- Migration audit: `python sync_core.py --audit` (strictly read-only)
- Local gates: Ruff, Pyright, coverage, and Pytest through `uv run`

The public facade and canonical submodules are snapshot-tested. Scientific golden
vectors cover metrics, bootstrap, calibration, Elo, ordinal, anti-lookahead, and the
Experiment Registry with explicit numeric tolerances. Contracts remain in the core
distribution to avoid duplicate type ownership.

No workflow checks out, commits to, or pushes a consumer repository. Consumer migration
is documented in `docs/MIGRATION_FROM_VENDOR.md`; consumers were intentionally not
modified in this repository change.
