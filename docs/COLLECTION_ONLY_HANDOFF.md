# COLLECTION_ONLY — contrato de coleta arquivística

`ObservationEnvelope` registra calendário, identidade, snapshot, resultado oficial,
proveniência e telemetria. É **COLLECTION_ONLY**: não é trial científico e não pode
promover um gate, calcular ROI/CLV ou autorizar capital.

Importe `predictor_core.contracts.collection`. Crie em `DISCOVERED`, grave em
`CollectionArchive` e avance com `transition`. Ordem: `DISCOVERED → VALIDATED →
SNAPSHOT_RECORDED → EVENT_STARTED → OFFICIAL_RESULT_FOUND → COMPLETE`.
`COMPLETE` exige resultado oficial. `REJECTED`, `SOURCE_UNAVAILABLE`,
`IDENTITY_AMBIGUOUS`, `STALE` e `CLOSED` são terminais e exigem motivo.

O JSONL é append-only: retries idênticos são idempotentes, mas não alteram o fato.
`collection_run_id` nunca é `trial_id`; não há estados científicos e
`as_scientific_trial()` sempre falha. Use `aggregate_funnel` por projeto, run e janela.

## Sincronização de vendors

Este documento não é vendorizado. O `CORE_MANIFEST.json` é gerado somente pelo sync
no vendor. Após revisão coordenada de cada consumidor, execute a partir do core:

```powershell
python sync_core.py --audit
```

Repita explicitamente para `lol-predictor`, `cs-predictor` e `f1-predictor`.
Não rode sync agora: esta entrega não edita consumidores. Vendors PARKED seguem
protegidos pelo script.
