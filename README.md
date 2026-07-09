# predictor_core — A Autoridade Canônica da plataforma

**Esta pasta é a FONTE DA VERDADE.** Toda a lógica compartilhada da plataforma de
previsão vive aqui e em nenhum outro lugar. Os domínios (`predictor-stocks`,
`previsao-cripto`, `wc-predictor-v2`) a consomem por **vendoring** — cópias carimbadas
em `vendor/predictor_core/` dentro de cada um.

Não há entrypoint. Não roda nada. É biblioteca de contratos.

## Os módulos

| Arquivo | Papel |
|---|---|
| `stats.py` | O **pedágio de 2 lentes**: PSR (Lente 1, closed-form, não-normalidade) + `block_bootstrap_ci` pareado (Lente 2, autocorrelação + cross-correlação). Mais `sharpe`/`sortino`/`max_drawdown`/`ci_mean`. |
| `infra.py` | SQLite isolado: `connect` (WAL + busy_timeout), `run_migrations` idempotente, `config_hash`. |
| `net.py` | Rede unificada: download stdlib (COTAHIST) + camada async resiliente (httpx lazy + retry/transient para REST CoinGecko/SerpAPI/LLM). |
| `obs.py` | Observabilidade + **telemetria JSONL** (`emit_event`, envelope rígido de 7 chaves; `read_events`). |
| `settings.py` | Trava P0 de credenciais (`require_secrets`): chave ausente/falsa/`<16` chars => crash imediato (pydantic + fallback stdlib). |
| `replay.py` | Anti-lookahead ESTRUTURAL ("feed, don't query"): `replay`/`PastView` — acessar o futuro levanta `LookaheadError`. |
| `measurement/trials.py` | **Experiment Registry** (reconciliado do previsao-cripto, v1.1.0): `validate_trials` (schema), `register_trial` com governança N+1 (mudar params = tentativa nova) e **trava de poder** — trial NOVA exige atestado do harness. + Deflated Sharpe Ratio. |
| `testing/harness.py` | Controle positivo (edge plantado detectado + ruído rejeitado) e `attest_pipeline_power`, que emite o atestado exigido pelo registry. |
| `data/contracts.py` | Envelopes da fronteira de dados (`MarketDataPoint`, `SignalPoint`) e **`PredictionPoint`** (v1.1.0) — o ciclo previsão→maturação→resultado com invariante anti-lookahead. |
| `sync_core.py` | O **motor de distribuição** (tooling — não faz parte do payload; `--write` faz prune do que sai do core). |
| `VERSION` | Carimbo da versão homologada. |

Suíte do core: **145 testes** (v1.1.0-ga-20260709). Histórico de API: `CHANGELOG.md`.

## A regra de ouro: escrita UNIDIRECIONAL

```
        edita aqui ─────────────►  sync_core.py --write  ─────────────►  <domínio>/vendor/predictor_core/
   (predictor_core/, a verdade)      (lê, calcula hash, sobrescreve)        (cópia carimbada, read-only)
```

Você **nunca** edita a matemática dentro do stocks ou do cripto. Corrige aqui, roda o
sync, e a correção propaga com integridade garantida. Isso elimina o **drift** — a
divergência de código que era dívida técnica latente (3 implementações de `connect`,
2 de `config_hash`, etc.).

## Uso

```powershell
py -3.12 sync_core.py --check     # relata o drift de cada consumidor (não escreve)
py -3.12 sync_core.py --write     # propaga o núcleo para os vendors (grava CORE_MANIFEST.json)
```

`--write` grava em cada vendor um `CORE_MANIFEST.json` (hash por arquivo + agregado +
timestamp + VERSION de origem). O `--check` confere esse agregado contra o canônico —
qualquer adulteração de um vendor (alguém "consertou" a matemática dentro de um
domínio para mascarar um resultado) aparece como **DRIFT**.

## Salvaguardas

- O sync só escreve em domínios que **já** têm `vendor/predictor_core/` (opt-in).
- Domínios **PARKED** (hoje: `wc-predictor`, em coleta da Copa até 19/07 — dado
  irreproduzível) **nunca** são escritos, mesmo que tenham vendor.
- A evolução do núcleo é "por demanda": precisou de uma peça (ex.: o PSR), implementa
  AQUI, bumpa o `VERSION`, roda o sync.
