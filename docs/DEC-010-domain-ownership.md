# DEC-010: ownership after the 3.0 boundary

Status: resolved; supersedes the ownership claims in ADR-002 and pre-3.0 changelog
entries where those entries describe symbols removed in 3.0.

Promotion requires a second real consumer or a concrete cross-domain contract. History
alone is not evidence of reuse.

| Primitive | Current location | Real Core consumers | Cross-domain reuse | Decision | Historical status |
|---|---|---:|---|---|---|
| Shin devig | domain-owned/absent from Core | 0 | not demonstrated | remain domain-owned | removed in 3.0 |
| Platt/isotonic | domain-owned/absent from Core | 0 | not demonstrated | remain domain-owned | removed in 3.0 |
| Elo/rating | domain-owned/absent from Core | 0 | not demonstrated | remain domain-owned | removed in 3.0 |
| null reference | domain-owned/absent from Core | 0 | not demonstrated | remain domain-owned | removed in 3.0 |
| interval coverage helper | domain-owned/absent from Core | 0 | not demonstrated | remain domain-owned | removed in 3.0 |
| ordinal/Plackett-Luce | domain-owned/absent from Core | 0 | not demonstrated | remain domain-owned | removed in 3.0 |
| economic contracts/ledger | domain-owned/absent from Core | 0 | not demonstrated | remain domain-owned | ADR-002 superseded |
| as-of adapter | domain-owned; Core retains replay cutoff | 0 shared adapters | semantics vary | keep adapter in domain | removed in 3.0 |
| stress/property helpers | domain-owned/standard test tooling | 0 | no Core contract | do not restore | removed in 3.0 |

Core retains neutral metrics, bootstrap/statistical primitives, prequential evaluation,
the positive-control harness, temporal replay, and trial provenance/multiplicity facts.
Permutation/placebo generation and synthetic-signal meaning remain domain-owned because
their exchangeability and causal assumptions depend on the dataset.
