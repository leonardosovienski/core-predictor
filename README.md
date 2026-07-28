# predictor_core — A Autoridade Canônica da plataforma

**Esta pasta é a FONTE DA VERDADE.** Toda a lógica compartilhada da plataforma de
previsão vive aqui e em nenhum outro lugar. Cinco consumidores vivos
(`brasileirao-predictor`, `cs-predictor`, `f1-predictor`, `lol-predictor` e
`previsao-cripto`) e três consumidores com vendor protegido
(`wc-predictor-v2`, `predictor-stocks` e `nba-predictor`) a consomem por
**vendoring** — cópias carimbadas em `vendor/predictor_core/` dentro de cada um.

Não há entrypoint de runtime — é biblioteca de contratos. Tem suíte própria
(`tests/`, 5 testes do `sync_core`): `C:\Claude\.venv\Scripts\python.exe -m pytest tests/ -q`.

## Os módulos

| Arquivo | Papel |
|---|---|
| `stats.py` | O **pedágio de 2 lentes**: PSR (Lente 1, closed-form, não-normalidade) + `block_bootstrap_ci` pareado (Lente 2, autocorrelação + cross-correlação). **`calibrated_ci`** = Lente 2 CALIBRADA (intervalo-t por blocos; cobertura medida 94-97% em AR(1), vs 85-93% liberal do percentil) — usar onde se AFIRMA significância. Mais `sharpe`/`sortino`/`max_drawdown`/`ci_mean` e quantis stdlib (`_normal_ppf`/`_t_ppf`). |
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

Suíte do core: **263 testes** (verificado 2026-07-18; ver `HANDOFF.md` para o
que mudou desde os 221 citados aqui originalmente — 8 correções PC-1 a PC-8
em `PredictionPoint`, `TrialRegistry` e `data/quality.py`, todas testadas).
Histórico de API: `CHANGELOG.md`. Continuidade operacional: `HANDOFF.md`.

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
python sync_core.py --check     # relata o drift de cada consumidor (não escreve)
python sync_core.py --write     # propaga o núcleo para os vendors (grava CORE_MANIFEST.json)
```

`--write` grava em cada vendor um `CORE_MANIFEST.json` (hash por arquivo + agregado +
timestamp + VERSION de origem). O `--check` **re-hasheia os bytes reais** de cada
vendor e compara arquivo a arquivo contra o canônico — qualquer adulteração de um
vendor (alguém "consertou" a matemática dentro de um domínio para mascarar um
resultado) aparece como **ADULTERADO** (manifest jura sincronia, bytes divergem);
vendor de versão antiga aparece como **DRIFT**.

## Salvaguardas

- O sync só escreve em domínios que **já** têm `vendor/predictor_core/` (opt-in).
- Domínios **PARKED** (atualizado 2026-07-18 — a lista acima estava
  desatualizada, citava só `wc-predictor`): hoje são exatamente três —
  `wc-predictor-v2`, `predictor-stocks`, `nba-predictor` — declarados em
  `sync_core.py:51` (`PARKED = {"wc-predictor-v2", "predictor-stocks",
  "nba-predictor"}`). **Nunca** são escritos por `--write`, mesmo com
  `--target` explícito (`_is_parked()` é checado antes de qualquer escrita,
  independente de como o consumidor foi selecionado) — confirmado por
  leitura de código e por teste de regressão em `tests/test_sync_core.py`.
  Histórico: essa lista já ficou vazia por engano entre 2026-07-03 e
  2026-07-17 (commit `15b6ada` corrigiu; ver `PENDENCIAS_ABERTAS.md` e
  `FINAL_FORENSIC_REVIEW.md` para o incidente).
- A evolução do núcleo é "por demanda": precisou de uma peça (ex.: o PSR), implementa
  AQUI, bumpa o `VERSION`, roda o sync.
