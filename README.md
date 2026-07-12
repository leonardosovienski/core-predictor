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
| `measurement/ledger.py` | **Ledger generalizado** (beancount-like, v1.2.0): `Posting`/`Transaction` de partida dobrada (soma zero, imutável) + `Ledger` append-only com `balance`/`balances`/`history`. Unifica o padrão de `bet_log` e `close_trial_sharpes`. |
| `kernel/rating.py` | **EloEngine unificado** (trueskill-like, v1.2.0): `expected_score`/`update_pair` (Elo par-a-par, soma-zero) + `RatingBook` (estado, K dinâmico, `record_ranking` para resultados multi-entidade — corridas, standings). |
| `measurement/ordinal.py` | **Camada ordinal** (choix-like, v1.2.0): Plackett-Luce — `plackett_luce_prob`, `fit_plackett_luce` (MLE via MM algorithm de Hunter 2004), `rank_probabilities`. Insumo para `rps` em resultados ranqueados (F1, LoL). |
| `testing/stress.py` | **Telemetria de estresse** (Hypothesis-like stdlib, v1.2.0): `check_property` roda uma propriedade contra amostras aleatórias determinísticas (`floats`/`integers`/`lists_of`), reportando o primeiro contraexemplo via `PropertyFailure`. |
| `contracts/` | **Camada de Tipagem Pura** (v1.3.0): fachadas canônicas — `contracts.points` (envelopes) e `contracts.registry` (governança N+1). Mesmos objetos das implementações físicas; novo código importa daqui. |
| `kernel/timeindex.py` | **Fronteira ISO/UTC** (v1.3.0): `utcnow`/`to_utc`/`iso_z`/`parse_iso`. Naive datetime cruzando fronteira = `NaiveDatetimeError` (nunca adivinha fuso). |
| `kernel/jsonl_store.py` | **`JsonlStore`** (v1.3.0): eventos append-only com leitura streaming; corrupção explícita com nº da linha; sem update/delete (correção é registro novo). |
| `measurement/calibration.py` | **Calibração** (v1.3.0): `PlattCalibrator` + `shin_devig` — decoradores matemáticos PUROS, chamados na última milha do consumidor (o core não força calibração no PredictionPoint: LoL refutou o Platt, CS comprovou). |
| `testing/prequential.py` | **Walk-forward via Template Method** (v1.3.0): `PrequentialEvaluator` (ABC) — o core controla o fatiamento (anti-leakage por construção: train só vê o passado, predict não vê o target); o consumidor implementa `train_step`/`predict_step`. |
| `sync_core.py` | O **motor de distribuição** (tooling — não faz parte do payload; `--write` faz prune do que sai do core). |
| `VERSION` | Carimbo da versão homologada. |

Suíte do core: **200 testes** (v1.3.0). Histórico de API: `CHANGELOG.md`.

**Punição global (v1.3.0)**: `attest_pipeline_power(..., metric="rps")` grava a métrica
no atestado; `register_trial(..., metric="rps")` exige match — harness atestado com
Brier não cobre veredito RPS (`MetricMismatchError`). `get_impersonating_session`
(kernel/net) traz curl_cffi LAZY: só quem raspa HLTV/SofaScore precisa da dependência.

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
