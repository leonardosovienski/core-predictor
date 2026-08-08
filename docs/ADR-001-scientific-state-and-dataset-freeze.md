# ADR-001: operational runs and scientific evidence are separate contracts

Status: accepted, 2026-08-08.

`predictor-ops` owns execution outcomes only. A successful process may carry a
scientific state such as `COLLECTION_ONLY` or `PENDING_SAMPLE`, but the runner
does not interpret or promote it.

`predictor-core` owns scientific transitions, acquisition charters and sealed
dataset freezes. A collection-only dataset cannot jump directly to a verdict:
hypothesis registration and a dataset freeze must precede shadow evaluation.

`DatasetFreeze.manifest_hash` is a deterministic SHA-256 integrity seal, not an
identity signature. Authentication may be layered on the sealed manifest by a
release or deployment system without putting key management in the core.

Domain repositories instantiate these contracts and retain responsibility for
providers, features, hypotheses and capital policy.
