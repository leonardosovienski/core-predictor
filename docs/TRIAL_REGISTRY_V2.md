# Trial Registry V2 contract

`TrialRegistryV2` is the prospective writer. Every row carries all fields in
`TRIAL_V2_FIELDS`; omission is an error. `UNKNOWN` is accepted only while validating a
legacy migration. `NOT_APPLICABLE` states that a concept genuinely does not exist and
is not a substitute for missing provenance. The legacy `TrialRegistry` remains readable
and is not silently upgraded.

The schema records experiment, hypothesis family and trial identity; registration and
execution time; seed, horizon, cutoff and label interval; dataset hash/version; feature,
model and code versions; parameters; selection path; family/domain/ecosystem attempt
counts; metric, result, status and notes. `selection_path` minimally records its family,
candidate set, selection metric and selected candidate. Thresholds and preceding trials
may be included in the same JSON object.

Attempt counts accept a positive integer or a conservative lower bound such as
`known_trials >= 29`. These are audit facts, not an instruction to use the ecosystem
count as every statistical correction's denominator. Analysis chooses the relevant
selection space and must justify it.

`dataset_fingerprint(rows, fields=..., order_matters=...)` hashes canonical UTF-8 JSON
of the selected fields from every actual row. Mapping keys are sorted, whitespace and
NaN/Infinity are forbidden, and row order matters unless explicitly disabled. Hashing
a config or query in place of the materialized data violates this contract.

`current_code_version()` reports package version plus the real Git commit and dirty
state when run in a checkout. It never manufactures a SHA. `migrate_legacy_registry`
writes to a distinct destination, is idempotent, validates its output in legacy mode,
copies only recorded facts, and marks everything else `UNKNOWN`.

Negative-control implementations (permutation/placebo) and synthetic-signal design are
domain-owned; the Core supports them through deterministic seeds, metrics, replay and
the prequential/harness hooks. Cutoff, availability and future visibility are Core-owned.
