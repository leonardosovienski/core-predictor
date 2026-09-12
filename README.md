# predictor-core

<!-- DOC-SYNC-20260912 -->
> **Estado de publicação em 12/09/2026:** leia [a continuidade atual](PUBLICATION_STATUS_20260912.md). Branch `validation/retest-six-20260911`. Este projeto não recebeu alterações de código na remediação CAIN Supply. Esta rodada atualiza somente documentação; versões e validações anteriores conservam seu escopo. Afirmações anteriores de “sem push” descrevem a etapa histórica anterior à autorização.
<!-- /DOC-SYNC-20260912 -->


## Entrega arquitetural publicada — 11/09/2026

Versão **3.2.1** publicada: [release e artefatos](https://github.com/leonardosovienski/core-predictor/releases/tag/v3.2.1). [CI de engenharia aprovada](https://github.com/leonardosovienski/core-predictor/actions/runs/34627786114) para a fonte `7bb212cfa06333886e11e849b209c5aab801c04b`. Consulte [ARCHITECTURE_IMPLEMENTATION.md](ARCHITECTURE_IMPLEMENTATION.md) para comportamento, migração e limites. Este registro atualiza a entrega de software; estados científicos e registros datados abaixo conservam sua autoridade e contexto histórico.

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
