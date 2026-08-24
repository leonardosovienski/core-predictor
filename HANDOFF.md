# Handoff

`predictor-core` is now a conventionally packaged scientific library.

- Source: `src/predictor_core/`
- Version source: `project.version` in `pyproject.toml` (`2.3.0`)
- Baseline: Python 3.13; Python 3.14 experimental
- Resolver/build: `uv.lock` and `uv build --wheel`
- Distribution: installed wheel only; vendoring is legacy
- Migration audit: `python sync_core.py --audit` (strictly read-only)
- Local gates: Ruff, Pyright, coverage, and Pytest through `uv run`

The public facade and canonical submodules are snapshot-tested. Scientific golden
vectors cover metrics, bootstrap, calibration, Elo, ordinal, anti-lookahead, and the
Experiment Registry with explicit numeric tolerances. Contracts remain in the core
distribution to avoid duplicate type ownership.

The boundaries of the shared temporal contract are recorded in
`docs/TEMPORAL_CONTRACT.md`. In particular, the Core owns `PredictionPoint` and the
feed-only `replay`; domain cutoffs, publication-time evidence, result recovery,
identity, metrics, and domain-specific hashes remain consumer responsibilities.

The current economic contract chain is `ProbabilisticForecast → MarketQuote →
EconomicDecision → ExecutionRecord → SettlementRecord`. It is domain-neutral and does
not authorize capital, choose sizing, or decide whether a hypothesis is profitable.
Those responsibilities remain outside Core by design.

No workflow checks out, commits to, or pushes a consumer repository. Consumer migration
is documented in `docs/MIGRATION_FROM_VENDOR.md`; consumers must consume released
artifacts rather than vendor copies in the modern architecture.
