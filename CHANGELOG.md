# Changelog — predictor_core

Formato de versão: `MAJOR.MINOR.PATCH-tag-YYYYMMDD` (o `-tag-data` é o carimbo de
procedência do sync; o `test_vendor_version_readable` do stocks valida o formato).
Dentro de um MAJOR: mudanças **aditivas**; remoção de símbolo público exige bump de
MAJOR + shim de deprecação por ≥1 ciclo MINOR.

Rumo à **v1.0.0** (plataforma pronta para produção) conforme
`docs/DESIGN_V1.md` — implementação por ondas (0→5). **v1.0.0 alcançada na Onda 5.**

## [1.3.0-ga-20260711] — estado definitivo: contratos, calibração, prequential, punição global

Consolidação do masterplan "100% de maturidade arquitetural". A topologia física
`src/` do design foi adiada (mover arquivos quebraria os imports dos 8 vendors —
exigiria MAJOR); TODA a lógica nova entrou de forma aditiva no layout atual, e o
pacote `contracts/` dá o caminho de import canônico novo via fachadas.

### Adicionado
- **`contracts/`** (Camada de Tipagem Pura): fachadas `contracts.points`
  (MarketDataPoint, SignalPoint, PredictionPoint) e `contracts.registry`
  (TrialRegistry, governança N+1) — mesmos objetos das implementações físicas
  (`data/contracts.py`, `measurement/trials.py`), que permanecem onde os
  vendors as importam.
- **`kernel/timeindex.py`** (Onda 1): fronteira ISO/UTC canônica — `utcnow`,
  `to_utc` (naive → `NaiveDatetimeError`, nunca adivinha fuso), `iso_z` (o
  formato exato do trials.json), `parse_iso`.
- **`kernel/jsonl_store.py`** (Onda 1): `JsonlStore` append-only com leitura
  streaming, `count`/`tail`, corrupção explícita com número da linha, e
  serialização validada ANTES da escrita (nunca deixa linha truncada).
- **`kernel/net.py` — lazy curl_cffi** (Padrão A): `get_impersonating_session`
  importa curl_cffi SÓ dentro da função — consumidores offline vendorizam o
  módulo sem a dependência; erro de import diz o que instalar e por quê.
- **`measurement/calibration.py`** (Onda 2, Padrão C): `PlattCalibrator`
  (regressão logística 1D stdlib, fit determinístico, decorator matemático
  puro — o core NÃO acopla ao PredictionPoint: LoL refutou, CS comprovou) e
  `shin_devig` (remoção de margem por Shin 1993 via bisseção; corrige o
  favourite-longshot bias que a normalização proporcional ignora; sem margem →
  proporcional).
- **`testing/prequential.py`** (Onda 2, Padrão B — Template Method):
  `PrequentialEvaluator` (ABC) controla o fatiamento walk-forward; o consumidor
  implementa `train_step`/`predict_step`. Anti-leakage POR CONSTRUÇÃO:
  train recebe só o passado estrito, predict recebe as features SEM o
  `target_key`. `min_history` e `retrain_every` para calendários distintos.
- **Punição global (harness ↔ registry, métrica-aware)**:
  `attest_pipeline_power(..., metric=...)` grava a métrica atestada;
  `register_trial(..., metric=...)` exige que a trial nova declare a MESMA
  métrica do atestado — mismatch levanta **`MetricMismatchError`**
  (subclasse de `PowerAttestationMissingError`; omitir `metric` preserva o
  comportamento v1.1.0). Um harness atestado com Brier não cobre vereditos RPS.
- Re-exports novos no `__init__.py`: `PlattCalibrator`, `shin_devig`, `utcnow`,
  `to_utc`, `iso_z`, `parse_iso`, `NaiveDatetimeError`, `JsonlStore`,
  `PrequentialEvaluator`, `MetricMismatchError`.

### Não mudou (Matriz de Responsabilidade)
- O core segue sem emitir SQL — SQLite pertence ao consumidor.
- `CircuitBreaker` já estava unificado em `data/circuit_breaker.py` (v1.0.0);
  não foi duplicado em `kernel/net.py`.
- Ledger permanece sem exclusão: correção = Posting de estorno (v1.2.0).

Suíte do core: **169 → 200** (31 testes novos).

## [1.2.0-ga-20260711] — Ledger + EloEngine + camada ordinal + telemetria de estresse

Onda de agosto/2026 do masterplan de arquitetura preditiva: quatro componentes
inspirados em repositórios abertos maduros, reimplementados stdlib-first (zero
dependências novas) para manter o princípio de dependências mínimas do core.

### Adicionado
- **`measurement/ledger.py`** (inspirado em beancount): contabilidade de partidas
  dobradas agnóstica de domínio. `Posting` (imutável), `Transaction` (grupo de
  postings que soma zero — `UnbalancedTransactionError` se violar), `Ledger`
  append-only (`post`, `balance`, `balances`, `history`). Unifica o padrão que
  `bet_log` (wc-predictor) e `close_trial_sharpes` (previsao-cripto)
  reimplementavam cada um a seu modo.
- **`kernel/rating.py`** (inspirado em trueskill/Elo): motor de ratings
  generalizado. `expected_score`/`update_pair` (Elo par-a-par clássico, delta
  soma-zero) + `RatingBook` (estado com K-factor fixo ou dinâmico via callback,
  `record_match` par-a-par e `record_ranking` para resultados multi-entidade —
  corrida de F1, standings de LoL — decompostos em pares com K normalizado por
  N-1). Não é TrueSkill bayesiano completo; é a abstração Entity/Context
  suficiente para CS, LoL, F1 e NBA nativamente.
- **`measurement/ordinal.py`** (inspirado em choix): camada Plackett-Luce.
  `plackett_luce_prob` (probabilidade de um ranking completo dado forças
  latentes), `fit_plackett_luce` (MLE via MM algorithm de Hunter 2004 — mesma
  base do `choix.ilsr`), `rank_probabilities` (normalização de Luce). Insumo
  direto para `measurement.metrics.rps` em domínios com resultado ranqueado
  (F1, LoL) — RPS já existia (v1.1.0), esta é a camada de estimação de força
  que faltava antes dele.
- **`testing/stress.py`** (inspirado em Hypothesis): telemetria de estresse
  property-based reimplementada em stdlib puro (sem adicionar `hypothesis`
  como dependência). `floats`/`integers`/`lists_of` (estratégias) +
  `check_property` (roda N amostras determinísticas por seed contra uma
  propriedade, levanta `PropertyFailure` com o primeiro contraexemplo
  reproduzível). Injeta casos extremos nas réguas do core além dos exemplos
  fixos das suítes.
- Re-exports no `__init__.py` da raiz: `Posting`/`Transaction`/`Ledger`/
  `UnbalancedTransactionError`, `Entity`/`expected_score`/`update_pair`/
  `RatingBook`, `plackett_luce_prob`/`fit_plackett_luce`/`rank_probabilities`,
  `check_property`/`floats`/`integers`/`lists_of`/`PropertyFailure`.

Suíte do core: **145 → 169** (24 testes novos: ledger, rating, ordinal, stress).

## [1.1.0-ga-20260709] — reconciliação do trials + PredictionPoint + trava de poder

Meta-auditoria da plataforma (2026-07-09): o `measurement/trials.py` do core tinha
ZERO consumidores enquanto o previsao-cripto evoluía uma cópia paralela — drift de
governança dentro de casa. Reconciliado: a versão evoluída do cripto é agora a canônica.

### Adicionado
- **`validate_trials`** (schema formal) e **governança N+1** em `register_trial`:
  mudar `params` de trial existente é `ValueError` (variação de configuração =
  tentativa nova) — antes o update era silencioso. Campos opcionais tipados
  (`features_used`, `train_period`, `test_period`). `TrialRegistry.validate()`.
- **Trava de poder (harness ↔ registry)**: criar trial NOVA exige atestado de
  controle positivo — arquivo irmão `<trials>.harness_attestation.json` emitido por
  **`testing.harness.attest_pipeline_power`** (roda o controle e grava; reprovou →
  não grava). Atualizar sharpe/notes de trial existente NÃO exige (maturação
  automática não depende do harness na mesma máquina). Bypass explícito
  `power_attestation=False` só para teste de mecânica. Novos símbolos:
  `PowerAttestationMissingError`, `attestation_path_for`.
- **`data.contracts.PredictionPoint`**: contrato do ciclo previsão→maturação→
  resultado (`predicted_at`, `matures_at`, `value`, `metadata`, `is_mature`) — o
  padrão implícito no bet_log do wc e no close_trial_sharpes do cripto. Invariante
  `matures_at >= predicted_at` (lookahead barrado na construção).

### Semântica endurecida (consumidores do símbolo antigo: zero — medido)
- `register_trial` não aceita mais update silencioso de `params`.
- `close_trial_sharpes` NÃO subiu: é lógica de domínio (estratos de Fonte, limiar
  de score) — permanece no cripto, consumindo o `register_trial` canônico.

Suíte do core: **129 → 145**.

## [1.0.1-ga-20260703] — guard de vazamento de segredos na telemetria

Último item do checklist de plataforma sob controle do core. Agregado: **`5e88ab46d86ef432`**
(33 arquivos; +`testing/secrets.py`). Suítes: core **129** · Copa **180** · cripto **171**(+2)
· stocks **103**.

### Adicionado
- **`testing/secrets.py`**: `find_secrets(text, known_values)` (padrões de prefixo de
  credencial conhecidos — sk-/AIza/ghp_/AKIA/Bearer/… — + match verbatim de valores reais
  do ambiente) e `assert_no_secrets_in_events(path)` — transforma um segredo no `metadata`
  do `emit_event` em falha de `pytest`, barrando o vazamento antes do commit.
- Teste do core (controle positivo: pega credencial plantada, passa em texto limpo,
  levanta em JSONL com segredo). 3 testes de domínio (`test_secrets_telemetry.py` em
  cripto/stocks/Copa). Conftest da Copa passou a ligar `vendor/` no path dos testes.

### Verificação
- Scan da telemetria REAL: cripto (122KB) → **0 achados**, Copa (41KB) → **0 achados** —
  sem vazamento acumulado e sem falso-positivo (o guard não é ruído).

## [1.0.0-ga-20260703] — Onda 5: reintegração do wc-predictor + v1.0.0

Agregado do payload: **inalterado no conteúdo** (só o VERSION mudou → novo agregado no
`--check`). **Os três domínios agora consomem o core** — `sync_core --check` limpo, 3/3,
**sem `DRIFT [PARKED]`**. Suítes: core **123** · stocks **100** · cripto **168** (+2) ·
**Copa 177**.

### Feito
- **wc-predictor DESPARKADO** (`sync_core.PARKED = set()`): a coleta (ingest→matches.db)
  é independente da análise; escrever `vendor/` é aditivo e não toca o SQLite congelado
  nem o config pré-registrado. A maquinaria de PARK permanece para uso futuro.
- **Vendor criado no wc-predictor-v2** (`vendor/predictor_core/`, 32 arquivos) + drift-test
  (`tests/test_core_integrity.py`, 4 testes). A Copa é agora consumidor de 1ª classe.
- **Removidos os scripts scratch mortos** da raiz da Copa: `stats.py`, `stats_corrigido.py`,
  `stats_final.py` — diagnósticos one-off de chutes/cartões (query a `matches.db`),
  **importados por nada** (grep confirmou zero referências). NÃO eram duplicatas do core.

### Deliberadamente NÃO migrado (honestidade de engenharia — evidência no HANDOFF da Copa)
- **`src/bootstrap.py`** — CLI numpy autocontido, **listado nos comandos operacionais do
  playbook pré-registrado**; sua RNG (numpy) difere da stdlib do core → um golden
  bit-a-bit é **impossível** e trocá-lo mudaria o IC de CLV pré-registrado no meio da Copa.
- **`src/research/score_metrics.py`** — métricas de **tensores de placar (N,G,G)**
  específicas de futebol (a própria docstring diz que NÃO pertence ao core); importado por
  `survival_test.py`. É ontologia de domínio, não a régua genérica.
- Ambos ficam congelados até o post-mortem (mandato do `COPA_2026_PLAYBOOK.md`), quando
  serão reconciliados com validação por TOLERÂNCIA (não bit-a-bit — a RNG muda).

### Estado v1.0.0
Core estável e completo: kernel (infra/obs/settings/net/meta) · measurement (stats/
metrics/bootstrap/trials/nullref/replay — as 3 lentes do pedágio) · data (contracts/
router/circuit_breaker/aggregation/quality/asof) · testing (synth/coverage/harness).
Distribuição por vendoring com manifesto; 3/3 consumidores em sincronia; princípios
(extração por demanda, stdlib-first, falha explícita, replay determinístico) preservados.

## [0.11.0-wave4-20260703] — Onda 4: referência nula + estado as-of

Agregado do payload: **`dc33595f54fdc270`** (32 arquivos; +2 módulos aditivos, puros).
Suítes verdes: core **123** · stocks **100** · cripto **168** (+2 skips). Nenhuma API
existente mudou — adições isoladas.

### Adicionado
- **`measurement/nullref.py`** — a 3ª LENTE do pedágio (DESIGN do stocks §10 M5):
  - `random_portfolio_sequence(universe, n_positions, n_periods, turnover, seed)`:
    sequência de carteiras aleatórias com turnover EXATO (novos nomes vêm de
    universo−carteira, garantindo o overlap; levanta se o universo for pequeno demais).
  - `null_distribution(statistic, universe, n_positions, ...)`: distribuição nula
    ordenada de uma estatística sobre seleções aleatórias (descarta stat não-finita).
  - `tail_probability(observed, null, side)` e `percentile_of`: p-valor de posição —
    "o seletor está na CAUDA da distribuição de seletores aleatórios?" (p pequeno = skill).
- **`data/asof.py`** — `state_asof(events, reducer, dates, *, key, window, inclusive)`:
  reconstrução forward-only de estado ("o que eu sabia em t"). Generaliza o
  `ratings_asof` do wc-predictor (Elo pré-jogo) para qualquer domínio; o reducer só
  recebe eventos ANTERIORES a cada data (anti-lookahead estrutural, como o replay mas
  para snapshots em datas específicas). Janela relativa opcional (ex.: Elo de 6 anos).

### Testes (16 novos)
- nullref: turnover exato realizado (overlap), buy-and-hold (turnover 0), sem overlap
  (turnover 1), guarda de universo pequeno, seletor com skill na cauda superior (p<0.01)
  vs seletor mediano no miolo (0.4<p<0.6). asof: prefixo estritamente anterior,
  inclusive, janela exclui eventos velhos, key callable, reducer arbitrário.

## [0.10.0-wave3-20260703] — Onda 3: camada de dados point-in-time (DPL → core)

Agregado do payload: **`b0873e019e5d3b0a`** (30 arquivos; +6 do subpacote `data/`).
Suítes verdes após o sync: core **107** · stocks **100** · cripto **168** (+2 skips).
Paga a dívida da **ADR-002** do previsao-cripto (a DPL vivia no domínio).

### Adicionado — `predictor_core/data/` (contratos + infraestrutura; providers ficam nos domínios)
- **`contracts.py`**: `MarketDataPoint`, `SignalPoint` (ambos com `published_at`
  obrigatório e invariante temporal que falha explícito), `DataProvider`,
  `SignalProvider`, `DataUnavailableError`. Promovidos de `dpl/contracts.py` + `dpl/signals.py`.
- **`aggregation.py`**: `consensus_median`, `consensus_mean`, `twap` (fusão multi-fonte;
  `published_at` do consolidado = max → anti-lookahead preservado).
- **`circuit_breaker.py`**: **CircuitBreaker UNIFICADO** — une as duas implementações que
  o cripto carregava (`dpl/circuit_breaker.py` com `allow()`/telemetria/relógio injetável
  e `v3/circuit_breaker.py` com `can_attempt()`/`data_quality_score`). Superset com ambas
  as APIs + `CircuitOpenError`. **Decisão de contrato:** `state` é getter PURO (transição
  OPEN→HALF_OPEN em `allow()`/`can_attempt()`, não ao ler `state`) — resolve o conflito
  real entre as duas suítes; a produção da dpl (router) usa `allow()`, comportamento
  idêntico. 2 asserts de `test_dpl_aggregation` reordenados para disparar via `allow()`.
- **`router.py`**: `FallbackRouter` (sequencial), `AggregationRouter` (consenso concorrente,
  tolera falha parcial). Promovidos de `dpl/router.py`.
- **`quality.py`**: `overnight_returns`, `detect_jumps`, `infer_split_factor`,
  `adjusted_closes` — funções puras promovidas do padrão do stocks (`src/adjust.py`).

### Migração do cripto (via shims — logic de-duplicada, sem reescrever ~30 import sites)
- `dpl/contracts.py`, `dpl/signals.py`, `dpl/aggregation.py`, `dpl/router.py`,
  `dpl/circuit_breaker.py` e `v3/circuit_breaker.py` viraram **shims** que reexportam do
  core. A DUPLICAÇÃO dos dois circuit breakers foi eliminada (uma só implementação, no
  core; os dois arquivos agora apontam para ela). 30 pontos de import intactos.

### Deferido com justificativa (princípios imutáveis)
- **FeatureStore NÃO promovido.** Ele não é puro core (carrega métodos de domínio:
  `predictions`, `fonte_label`, migração 0006) e tem UM só consumidor. Promovê-lo agora
  violaria "extração por demanda / nenhuma abstração prematura" e exporia os 168 testes a
  um split arriscado. Fica para quando o stocks exigir armazenamento bitemporal (2º consumidor).

### Testes (tests/test_data/, 29 novos)
- contracts (invariantes temporais), aggregation (fusão + published_at=max), circuit_breaker
  (os 7 comportamentos da máquina de estados unificada + `allow()` + relógio injetável),
  router (fallback, skip de breaker aberto, consenso sobre sobreviventes, DataUnavailableError),
  quality (detecção de salto, split/grupamento, série contínua). Async via `asyncio.run`
  (sem pytest-asyncio — stdlib-first).

## [0.9.1-wave2-20260703] — Onda 2: harness de validação da régua

Agregado do payload: **`63335ff74b36ae98`** (24 arquivos; +4 do subpacote `testing/`).
Suítes verdes após o sync: core **78** · stocks **100** · cripto **168** (+2 skips).

### Adicionado — `predictor_core/testing/` (distribuído no payload)
- **`synth.py`**: geradores sintéticos com verdade conhecida — `ar1_series(n, phi,
  sigma, seed, mu)` (média de processo e autocorrelação conhecidas), `edge_injected`
  (desloca a média por um valor conhecido) e `probabilistic_predictor(n, skill_level,
  seed)` (skill 0 = uniforme, 1 = one-hot). **stdlib puro** (`random`/`math`,
  `list[float]`) — a spec sugeriu numpy, mas o core não carrega dependência externa
  obrigatória (princípio imutável stdlib-first; desvio justificado e semanticamente
  equivalente).
- **`coverage.py`**: `bootstrap_coverage(...)` (fração observada) + `coverage_in_band(...)`
  (True se em `confidence±tolerance`). Valida a Lente 2 por comportamento: um IC 95%
  cobre a verdade em ~95%. Regime travado (determinístico): iid/cluster ~0.94 em dado
  i.i.d.; moving/stationary ~0.96 sob AR(1) phi=0.2 (onde o iid na mesma série cobre só
  ~0.87 — o bloco recupera a autocorrelação). A função de veredito NÃO se chama `test_*`
  de propósito (evita coleta acidental pelo pytest em qualquer suíte que a importe).
- **`harness.py`**: `assert_pipeline_has_power(evaluate_func, edge_generator,
  noise_generator)` — controle positivo: exige que o pipeline DETECTE edge sintético
  (sensibilidade) e REJEITE ruído (especificidade); levanta `PipelineHasNoPowerError`
  se qualquer braço falhar. Sem passar, nenhum GO/NO-GO do pipeline é interpretável.

### Testes (tests/test_testing/, 15 novos)
- Determinismo dos geradores; cobertura em banda para os **4 esquemas**; **poder do
  próprio teste de cobertura** (iid sob phi=0.4 sub-cobre → `coverage_in_band` False);
  o bloco recupera a autocorrelação (moving >> iid na mesma série); controle positivo
  pega pipeline cego (sempre REFUTADA) e crédulo (sempre COMPROVADA).

### Nota
- Nenhuma API existente mudou; `testing/` é inerte para os consumidores (só importado
  quando eles escolherem usá-lo). A régua da Onda 1 está agora **blindada por
  propriedade mecânica** — pré-requisito para a Onda 3 (camada de dados).

## [0.9.0-wave1-20260703] — Onda 0 (CI/drift) + Onda 1 (camadas + régua completa)

Agregado do payload: **`50aaf9acc6d0ce9b`** (20 arquivos; antes `0f6ef2e1bdf06548`, 8
arquivos flat). O agregado mudou por DUAS razões esperadas: (a) as chaves do manifesto
passaram de nome-de-arquivo para caminho relativo POSIX; (b) 4 módulos novos entraram.
Suítes verdes após o sync: core 63 · stocks 100 · cripto 168 (+2 skips hmmlearn).

### Onda 0 — CI + drift-check
- **CI do canônico** (`.github/workflows/tests.yml`): matriz 3.13/3.14 × ubuntu/windows,
  roda `pytest tests/` + `sync_core.py --check`. Portão das ondas seguintes.
- **Drift-check nos consumidores** (`tests/test_core_integrity.py`): valida cada arquivo
  do vendor contra o `CORE_MANIFEST.json` (hash por caminho + agregado). Adulteração
  local, dessincronia ou órfão viram falha de `pytest`. Poder verificado: 1 byte
  alterado no vendor faz o agregado divergir.

### Onda 1 — estrutura em camadas
- **`sync_core.py` recursivo**: payload = todos os `*.py` (recursivo) + VERSION, chaves
  = caminho relativo POSIX; `cmd_write` cria subdiretórios e poda a árvore do vendor
  (órfãos + `__pycache__` + dirs vazios). `docs/`, `tests/`, `.github/` NÃO são payload
  (canônico-only — sem consumidor de runtime). `--check` não conta drift de domínio
  PARKED no exit code (congelamento é esperado, não falha). Saída reconfigurada p/
  UTF-8 (o console cp1252 do Windows quebrava em `≠`/`—`).
- **Camadas físicas**: `kernel/` (infra, obs, settings, net, meta) e `measurement/`
  (stats, bootstrap, metrics, trials, replay). Os módulos planos de topo
  (`predictor_core.stats`, `.obs`, ...) viram **shims de compat** que reexportam o
  namespace inteiro do módulo real — `from predictor_core.stats import ...` e o
  `import stats` flat dos testes seguem funcionando.
- `__init__.py`: re-exporta a API pública estável das camadas (`__all__`).

### Onda 1 — régua completa (módulos novos)
- **`kernel/meta.py`**: `fingerprint(schema_version, features, params)` + `validate`
  (levanta `StaleModelError` em incompatibilidade; avisa em legado). Unifica o
  fingerprint do `regime_engine` (cripto) e o `config_hash` (Copa).
- **`measurement/metrics.py`** (régua PROBABILÍSTICA, stdlib pura): `brier`, `log_loss`,
  `rps` (ordinal), `calibration_table`, `diebold_mariano` (correção HLN + p-valor
  t-Student via beta incompleta, sem numpy/scipy). Genérica — serve NBA/Eleições/Clima.
- **`measurement/bootstrap.py`**: `bootstrap_ci(series, statistic, scheme=...)` unifica
  `iid | moving | stationary | cluster`. O esquema `cluster` (promoção do `bootstrap.py`
  da Copa) reamostra clusters inteiros. `block_bootstrap_ci`/`ci_mean` permanecem em
  `measurement/stats.py` como **wrappers depreciados** (DeprecationWarning; delegam ao
  novo). Invariância do cluster coberta por teste (IC mais largo sob correlação intra).
- **`measurement/trials.py`**: `TrialRegistry` + `deflated_sharpe_ratio` (DSR sobre o
  PSR do core). Promoção do previsao-cripto; caminho do arquivo agora é do domínio.
- **`docs/HYPOTHESES.md`**: template de pré-registro (canônico-only).

### Retrocompatibilidade
- Todos os imports 0.8.0 seguem válidos via shims (`from predictor_core.stats import
  block_bootstrap_ci` etc.), inclusive símbolos privados. Nenhuma remoção; só adições e
  deprecações. Consumidores migram para os caminhos em camadas no seu ritmo.

## [0.8.0-redteam-20260625] — baseline auditado

Estado herdado das auditorias (Red Team). Payload flat de 7 módulos:
`infra`, `net`, `obs`, `settings`, `replay`, `stats`, `__init__` + `VERSION`.

- `stats.py`: régua financeira (Sharpe, Sortino, max_drawdown com contrato de equity
  curve), PSR (Lente 1, verificado contra QuantConnect/LEAN), `block_bootstrap_ci`
  (Lente 2: moving/stationary, unidades escalares ou pareadas, guards de reamostra
  inválida), `spearman`/`spearman_block_ci`, `ci_mean` (iid).
- `replay.py`: anti-lookahead estrutural (`PastView`/`LookaheadError`, ordem verificada).
- `infra.py`: SQLite WAL + migrações idempotentes + `config_hash`.
- `obs.py`: telemetria JSONL (envelope rígido de 7 chaves).
- `settings.py`: `require_secrets` fail-fast (pydantic opcional, fallback stdlib).
- `net.py`: download bulk stdlib + REST async resiliente (httpx opcional).
- Distribuição: `sync_core.py` (vendoring unidirecional + `CORE_MANIFEST.json`);
  domínios PARKED (wc-predictor) nunca recebem escrita.
