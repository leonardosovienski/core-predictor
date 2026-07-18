# HANDOFF — predictor_core/

Verificado em: 2026-07-18. Commit-base: `9868c01` (branch `main`).

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

35 módulos, **263 testes passed** (verificado 2026-07-18, cache limpo).
5 vendors vivos byte-idênticos (`sync_core.py --check` e
`tools/vendor_byte_audit.py` confirmam). 3 vendors PARKED em drift
esperado, intocados. Nenhum bug de código conhecido em aberto.

## 4. Branch, versão e commit-base

Branch única `main`. `VERSION` = `1.3.1-ga-20260716`. Commit-base desta
verificação: `9868c01`.

## 5. Estado Git

Working tree limpo. Sem remoto configurado — nada publicado.

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
  core — são 3 implementações locais com garantias diferentes (CS tem
  vínculo criptográfico via hash, F1 e LoL não). `SHARED_BUT_INCUBATING`,
  não promovido (INC-1).

## 10. Decisões importantes

- **Não normalizar identidade no `RatingBook`**: normalizar
  (`.strip().lower()`) mudaria trajetórias de rating já calculadas —
  mudança científica, não permitida sem decisão humana explícita e sem 2º
  consumidor real comprovando a necessidade. Só `f1-predictor` usa
  `RatingBook` diretamente hoje.
- **Não promover lifecycle compartilhado**: 3 implementações convergem em
  conceito mas não em garantia (CS tem hash-linkage, F1/LoL não) —
  promover um enum comum esconderia essa diferença real.
- **PARKED repovoado em `15b6ada`** (2026-07-17): estava vazio desde
  2026-07-03 por decisão de uma sessão anterior de desparkar `wc-predictor`
  — a lista inteira ficou vazia por engano em vez de remover só esse nome,
  permitindo `--write` sem `--target` tocar os 3 protegidos. Corrigido,
  testado, os 3 protegidos revertidos (`git revert`, não reset).

## 11. Correções recentes

Ver `FINAL_FORENSIC_REVIEW.md` (commit `cca60f0`) para verificação
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
Resultado esperado: `263 passed`. Ver `RUNBOOK_TESTS.md` e
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

Ver `PENDENCIAS_ABERTAS.md` seções 4 e 5 (SCI-1 a SCI-4, INC-1) — todas
`CORRECTLY_DEFERRED`/`SHARED_BUT_INCUBATING`, nenhuma bloqueante.

## 17. Riscos

Ver seção 9 acima ("Limites explícitos, não bugs") e
`PENDENCIAS_ABERTAS.md` para a lista de riscos residuais com condição de
reabertura.

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

Nenhuma pendente que exija ação imediata. Rodar `RUNBOOK_VENDOR_SYNC.md`
antes de qualquer mudança futura no core, seguido de
`RUNBOOK_ARTIFACT_INTEGRITY.md` para confirmar preservação científica.
