# predictor-core

Canonical, installable scientific library for Predictor domains. The package uses a
standard `src/predictor_core` layout and does not depend on the checkout directory,
`PYTHONPATH`, sibling repositories, or vendored copies.

## Requirements and installation

Python 3.13 is the supported baseline. Python 3.14 is tested as experimental.

```bash
uv sync --frozen --group dev
uv run pytest
uv build --wheel
```

Consumers install a released artifact, for example:

```bash
uv add "predictor-core==3.1.0"
python -c "import predictor_core; print(predictor_core.__version__)"
```

Extras are capability-based: `http` provides `httpx`, `scraping` provides
`curl-cffi`, `science` is dependency-free today, and `test` provides the supported
test stack. Missing optional capabilities therefore fail at installation/resolution
when the corresponding extra is declared, rather than being an undocumented runtime
dependency.

The stable facade is `import predictor_core`; stable subpackages are `contracts`,
`data`, `kernel`, `measurement`, and `testing`. The flat package modules
`predictor_core.stats`, `.infra`, `.net`, `.obs`, `.replay`, and `.settings` remain
temporary compatibility shims. See [API compatibility](docs/API_COMPATIBILITY.md),
[migration](docs/MIGRATION_FROM_VENDOR.md), and [versioning policy](docs/VERSIONING.md).
The cross-domain temporal guarantees and consumer responsibilities are documented in
[Temporal contract](docs/TEMPORAL_CONTRACT.md).
Prospective experiment provenance is defined by the
[Trial Registry V2 contract](docs/TRIAL_REGISTRY_V2.md); the legacy registry remains
available only for compatibility and non-destructive migration.

Version 3.0 keeps only primitives with demonstrated cross-domain consumers.
Economic, rating, calibration, ordinal, ledger, null-reference, as-of and stress
helpers were removed; domains own those concerns until a second consumer exists.

The economic abstention gates currently used by Brasileirão, crypto and stocks are
domain-owned. Core supplies the temporal, statistical and prequential primitives used
to evaluate them, but it does not choose trades, bets, rebalances or capital state.

`sync_core.py --audit` is read-only and exists only to locate legacy vendor copies.
`--write` is permanently rejected. Distribution occurs through wheels.


## Implementação arquitetural local — 2026-09-11

As alterações candidatas, seus limites, verificações e rollback estão em [ARCHITECTURE_IMPLEMENTATION.md](ARCHITECTURE_IMPLEMENTATION.md). Esta implementação local não publica releases, não atualiza automaticamente os consumidores e não altera os vereditos científicos históricos.
