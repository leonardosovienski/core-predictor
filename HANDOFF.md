# HANDOFF — predictor_core/

Verificado em: 2026-07-29. Estado de trabalho: preparação da release 2.0.0.

## 1. Identidade

Camada científica canônica do ecossistema preditivo local. Biblioteca pura
(sem entrypoint, não roda nada sozinha) — contratos, mensuração,
governança de experimentos, compartilhados por vendoring.

## 2. Finalidade

Prover contratos temporais anti-lookahead (`PredictionPoint`,
`MarketDataPoint`, `SignalPoint`), governança de experimentos
(`TrialRegistry`, N+1), mensuração/estatística comum (bootstrap, PSR/DSR,
calibração, ordinal) e rating genérico (`RatingBook`) — só o que já provou
ser compartilhável entre pelo menos 2 domínios reais, nunca por semelhança
de nome.

## 3. Estado atual

40 arquivos `.py` fora de `tests/`, excluindo `__init__.py` — 33 módulos
reais, 6 compat shims na raiz (`infra.py`, `net.py`, `obs.py`,
`replay.py`, `settings.py`, `stats.py`, que só re-exportam de `kernel/`
e `measurement/`) e `sync_core.py` (distribuidor, não payload).
**273 testes coletados** na validação local de 2026-07-29.

4 dos 5 vendors vivos byte-idênticos, 46/46 arquivos cada (`sync_core.py
--check` e `tools/vendor_byte_audit.py` confirmam): `brasileirao-predictor`,
`cs-predictor`, `f1-predictor` e `lol-predictor`. `previsao-cripto` está em
DRIFT — vendor parado em `1.3.2-ga-20260720` (`synced_at 2026-07-20`),
44/46 arquivos, faltando `contracts/collection.py` e `data/collection.py`:
não recebeu a entrega 1.3.3. É atraso de sync, não adulteração — o manifest
do vendor é internamente coerente (agregado gravado = agregado real
`dc7676a61c86f908`). Por isso `sync_core.py --check` retorna exit 1.

3 vendors PARKED em drift esperado, intocados. Nenhum bug de código
conhecido em aberto.

## COLLECTION_ONLY (entrega 1.3.3)

`ObservationEnvelope` (`collection-only/1`) e `CollectionArchive` registram
calendário, identidades, snapshots, resultados oficiais, provenance e telemetria
em JSONL append-only. O lifecycle é monotônico e auditável; `COMPLETE` exige
resultado oficial. O contrato não aceita estados científicos, `collection_run_id`
não pode ser `trial_id` e `as_scientific_trial()` sempre falha.

Validado em 2026-07-25: 268 testes passaram. `sync_core.py --check` confirmou
brasileirao-predictor, lol-predictor, cs-predictor e f1-predictor byte-idênticos
ao canônico. Consulte `docs/COLLECTION_ONLY_HANDOFF.md`.

## 4. Branch, versão e commit-base

Branch única `main`. `VERSION` = `2.0.0-ga-20260729`.

## 5. Estado Git

Há mudanças locais ainda não commitadas da release 2.0.0. Remoto `origin` aponta para
`github.com/leonardosovienski/core-predictor`. `main` local está em
`11c4792`, **2 commits à frente** de `origin/main` (`969cad5`, pela ref
local — sem `fetch` em 2026-07-25): `2c5a040` (contrato COLLECTION_ONLY) e
`11c4792` (handoff) ainda não publicados.

## 6. Arquitetura

Ver `README.md` para a tabela completa de módulos. Núcleos: `data/contracts.py`
(`PredictionPoint`/`MarketDataPoint`/`SignalPoint`), `measurement/trials.py`
(`TrialRegistry`), `kernel/rating.py` (`RatingBook`), `data/asof.py`
(point-in-time), `data/quality.py` (detecção de salto/qualidade de dado),
`sync_core.py` (motor de distribuição vendoring — não é payload).

## 7. Fluxo de execução

`sync_core.py --write` (com `--target` para escopo por consumidor, ou sem
para todos os não-PARKED) copia o payload para
`<consumidor>/vendor/predictor_core/`. Nenhum consumidor edita a cópia
vendorizada — correção sempre na fonte (`predictor_core/`) seguida de sync.

## 8. Integrações

5 vivos vendorizam: brasileirao-predictor, cs-predictor, f1-predictor,
lol-predictor, previsao-cripto. 3 protegidos (`wc-predictor-v2`,
`predictor-stocks`, `nba-predictor`) vendorizam uma versão antiga,
congelada — nunca recebem `--write` (`PARKED` em `sync_core.py:51`).

## 9. Contratos

`PredictionPoint(predicted_at, matures_at, value, metadata)`: invariante
`matures_at >= predicted_at`, tipos validados (rejeita não-datetime desde
2026-07-17), naive/aware misto rejeitado com erro claro,
`__hash__`/`__eq__` consistentes (hash em `(predicted_at, matures_at)`
apenas). `MarketDataPoint`/`SignalPoint`: `published_at >= timestamp`
obrigatório (a âncora anti-lookahead real, com checagem cruzada — algo que
`PredictionPoint` **não tem** para seus próprios insumos, ver seção 10).
`TrialRegistry`: identidade por `name`, governança N+1 (params diferentes
= tentativa nova, nunca update silencioso), lock de arquivo com liveness de
PID desde 2026-07-17.

**Limites explícitos, não bugs:**
- `PredictionPoint` não prova que os dados usados para gerar `value` tinham
  `published_at <= predicted_at` — não há campo `observed_at`/`available_at`
  nem checagem cruzada. Gap de design real, documentado, não implementado
  (ver `PENDENCIAS_ABERTAS.md` SCI-2).
- `is_mature(now)` é só informativo — nada impede acesso a `.value` antes da
  maturação (SCI-3).
- `RatingBook` não normaliza identidade (`"Team A"` ≠ `"team a "`) —
  deliberado, normalizar mudaria ciência (SCI-1).
- Lifecycle `PRE_EVENT`/`MATURED` de CS/F1/LoL **não é** um contrato do
  core — são 3 implementações locais com garantias diferentes (CS e F1
  vinculam PRE_EVENT→MATURED por hash do payload; LoL vincula por
  `prediction_id`, sem hash do payload PRE_EVENT). `SHARED_BUT_INCUBATING`,
  não promovido (INC-1).

## 10. Decisões importantes

- **Não normalizar identidade no `RatingBook`**: normalizar
  (`.strip().lower()`) mudaria trajetórias de rating já calculadas —
  mudança científica, não permitida sem decisão humana explícita e sem 2º
  consumidor real comprovando a necessidade. Só `f1-predictor` usa
  `RatingBook` diretamente hoje.
- **Não promover lifecycle compartilhado**: 3 implementações convergem em
  conceito mas não em garantia (CS/F1 têm hash-linkage; LoL não) —
  promover um enum comum esconderia essa diferença real.
- **PARKED repovoado em `15b6ada`** (2026-07-17): estava vazio desde
  2026-07-03 por decisão de uma sessão anterior de desparkar `wc-predictor`
  — a lista inteira ficou vazia por engano em vez de remover só esse nome,
  permitindo `--write` sem `--target` tocar os 3 protegidos. Corrigido,
  testado, os 3 protegidos revertidos (`git revert`, não reset).

## 11. Correções recentes

Ver o histórico de commits, o CHANGELOG e os testes de regressão para verificação
detalhada — 8 correções nesta rodada (PC-1 a PC-8): validação de tipo em
`PredictionPoint` (`c88a14c`), rejeição de naive/aware misto (`c88a14c`),
`__hash__` estável (`c88a14c`), NaN/Inf em params de trial rejeitado
(`c44e3df`), erro claro para valor não-serializável (`c44e3df`), mensagem
distinguindo entrada legada malformada de trial nova (`c44e3df`), lock com
liveness de PID (`c44e3df`), `detect_jumps` reportando NaN em vez de
engolir silenciosamente (`9868c01`). Mais `15b6ada` (PARKED repovoado).

## 12. Testes e validações

```
cd predictor_core
python -m pytest -q
```
Resultado esperado: `268 passed`. Ver `RUNBOOK_TESTS.md` e
`RUNBOOK_VENDOR_SYNC.md`.

## 13. Automação

`predictor_core/` em si não tem automação agendada — é biblioteca. Ver
handoffs de cada consumidor para as automações que o vendorizam.

## 14. Artefatos

`CORE_MANIFEST.json` por vendor (hash por arquivo + agregado). `VERSION`.
Nenhum dado científico vive aqui — dados são dos consumidores (ver
`ARTIFACT_INVENTORY.md`).

## 15. Segurança

Sem incidente conhecido próprio. `settings.py::require_secrets` é a trava
de credenciais consumida por domínios que precisam de chaves externas.

## 16. Pendências

Não há pendências documentadas no repositório nesta release.

## 17. Riscos

Ver seção 9 acima ("Limites explícitos, não bugs") para riscos residuais e
condições de reabertura.

## 18. O que não fazer

Não normalizar identidade no `RatingBook` sem decisão humana. Não promover
lifecycle compartilhado por semelhança de nome. Não adicionar
`observed_at`/`available_at` a `PredictionPoint` sem desenhar o contrato
com cuidado (múltiplas soluções legítimas). Não tocar os 3 vendors PARKED.

## 19. Condições para reabrir decisões

`RatingBook`: 2º consumidor real ou typo real observado em produção.
Lifecycle: 4º domínio precisando do mesmo padrão E convergência de
garantias entre CS/F1/LoL. `observed_at`/`available_at`: incidente real de
lookahead reportado por um consumidor.

## 20. Próxima ação legítima

**Pendente: sincronizar o `previsao-cripto`** — é o único bloqueio aberto
(ver §3). Enquanto ele ficar em `1.3.2-ga-20260720`, `sync_core.py --check`
retorna exit 1. Note que o rollout da 1.3.3 em
`docs/COLLECTION_ONLY_HANDOFF.md` listou explicitamente só
`brasileirao-predictor`, `lol-predictor`, `cs-predictor` e `f1-predictor`:
decida se a omissão do `previsao-cripto` foi escopo deliberado ou lacuna
antes de agir. Após revisão coordenada do consumidor, seguindo
`RUNBOOK_VENDOR_SYNC.md`:

```powershell
python sync_core.py --check
python sync_core.py --write --target previsao-cripto
```

Nenhuma outra ação pendente: zero bug de código conhecido, zero teste
falhando, zero vendor adulterado. Rodar `RUNBOOK_VENDOR_SYNC.md` antes de
qualquer mudança futura no core, seguido de
`RUNBOOK_ARTIFACT_INTEGRITY.md` para confirmar preservação científica.
