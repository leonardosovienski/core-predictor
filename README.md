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
uv add "predictor-core==2.1.0"
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

`sync_core.py --audit` is read-only and exists only to locate legacy vendor copies.
`--write` is permanently rejected. Distribution occurs through wheels.
