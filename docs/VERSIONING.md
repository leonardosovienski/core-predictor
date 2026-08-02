# Versioning, compatibility, and deprecation

`project.version` in `pyproject.toml` is the single version source and follows SemVer.
`predictor_core.__version__` reads installed distribution metadata.

- Patch: compatible fixes with scientifically equivalent outputs within documented
  tolerances.
- Minor: backward-compatible API additions. Scientific behavior changes require a
  separately reviewed trial even when the API remains compatible.
- Major: removals or incompatible contract changes.

Public symbols are the root `__all__`, documented subpackages, and compatibility
modules listed in the API report. Deprecations emit `DeprecationWarning`, remain for
at least one minor release and 90 days, and include replacement and removal release.
Removal happens only in a major release unless a security flaw requires otherwise.

Python 3.13 is required. Python 3.14 remains experimental until locked installation,
typing, the complete suite, golden tests, and wheel smoke tests all pass in CI.
