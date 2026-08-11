# Temporal contract

This document defines the stable cross-domain temporal guarantees provided by
`predictor-core`. It records the boundary validated independently by the F1, League
of Legends, and Counter-Strike consumers; it does not add a new public API.

## Core guarantees

`PredictionPoint` represents a value emitted at `predicted_at` and eligible to mature
at `matures_at`. Both timestamps must be timezone-aware, `matures_at` cannot precede
`predicted_at`, and `is_mature(now)` applies that boundary consistently.

`replay` processes an ordered feed through `PastView`. A handler can observe only the
current and earlier events. Future indexing raises `LookaheadError`, and a supplied
time key must be monotonic. This is the structural anti-lookahead primitive.

These guarantees cover temporal representation and feed visibility. They do not
claim that a consumer selected the correct domain cutoff or knew when an external
source actually published an observation.

## Consumer responsibilities

Each consumer remains responsible for:

- defining the domain cutoff and mapping it to `predicted_at` and `matures_at`;
- proving when external inputs and outcomes became available;
- recovering and validating outcomes;
- defining event, participant, model, dataset, and prediction identity;
- selecting metrics and acceptance rules;
- choosing which payloads are canonicalized or hashed;
- preserving versioned fixtures and golden artifacts when deterministic replay is
  part of that consumer's evidence.

An adapter may translate those local concepts into `PredictionPoint` and ordered
replay events. The adapter is not part of the Core contract merely because several
consumers use the same Core primitives.

## What tests can demonstrate

Core tests demonstrate timestamp validation, maturation boundaries, monotonic replay,
and prevention of future access. Consumer tests can additionally demonstrate that a
specific adapter detects a violated cutoff and that a versioned golden diverges
deterministically when its inputs change.

Those tests do not establish the real publication instant of an external dataset,
scientific quality, statistical equivalence across domains, live behavior, or
economic value. Those claims require separate evidence owned by each consumer.

## Promotion rule

Canonicalization or hashing should become a Core API only after multiple independent
consumers require the same inputs, normalization rules, serialization, digest
algorithm, error semantics, and compatibility policy. The current cross-domain
evidence supports a reusable pattern, not that public API.
