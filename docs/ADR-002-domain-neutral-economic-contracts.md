# ADR-002: Domain-neutral economic contracts

Status: accepted

## Context

`PredictionPoint` intentionally accepts an opaque value. That is useful for temporal
maturation, but it cannot make forecasts, bookmaker quotes, exchange orders and
economic settlements comparable across LoL, CS, F1, football and future domains.
Consumers consequently invented incompatible representations for outcomes, odds,
liquidity, fills, costs and P&L.

## Decision

The Core owns an additive, zero-dependency contract chain:

```text
PredictionPoint (legacy-compatible temporal envelope)
    ↓
ProbabilisticForecast → MarketQuote → EconomicDecision
                                      ↓
                            ExecutionRecord → SettlementRecord
```

- `Market` and `Selection` supply stable cross-system identity while leaving sport and
  competition taxonomies to domains.
- `ProbabilisticForecast` is a complete normalized distribution. It records uncertainty
  intervals, strategy, dataset, model and the information cutoff.
- `MarketQuote` represents decimal back/lay price, executable size, optional line and
  spread, commission, closing status and the quote's availability timeline.
- `EconomicDecision` records the result of an external strategy/risk policy, including
  estimated edge and economic eligibility.
- `ExecutionRecord` preserves zero or more immutable fills and execution status.
- `SettlementRecord` reconciles gross P&L, costs and net P&L.
- `validate_economic_chain` verifica referências, outcomes, ordem temporal,
  compatibilidade back/lay e limites de fill entre records independentes.

All instants are timezone-aware and normalized to UTC. Contracts are frozen and reject
non-finite numbers. The schema family starts at
`ECONOMIC_CONTRACT_SCHEMA_VERSION = "1.0.0"` and is exported by both stable facades.

## Boundaries

The Core does **not** implement Kelly sizing, bankroll allocation, exposure limits,
approval workflows, source-specific market mapping, exchange matching, bookmaker
settlement rules or tax/accounting policy. Those belong to risk, governance, adapters
and domain services. The Core validates the portable record after those components make
their decisions.

`PredictionPoint` remains unchanged. Consumers can carry a `ProbabilisticForecast` as
its opaque `value` during migration, then adopt the richer stages independently.

## Consequences

Aggregators can compare forecasts, executable quotes and realized economics with the
same vocabulary across domains. Adapters must translate native identifiers and rules
at their boundary. A later major version may add serialization codecs or richer
multi-currency accounting, but must not silently reinterpret these v1 records.
