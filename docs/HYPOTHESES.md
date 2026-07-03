# Template de Pré-registro de Hipóteses — protocolo anti-data-snooping

> Template distribuído pelo predictor_core (promovido do previsao-cripto). Copie para
> o `docs/HYPOTHESES.md` do seu domínio e preencha. Complementa o `TrialRegistry`
> (`measurement.trials`): o registro conta as tentativas (denominador do DSR); este
> arquivo registra o que cada tentativa ESPERAVA encontrar e qual era o critério de
> sucesso — para que um resultado positivo futuro não possa ser reescrito como "era o
> que sempre buscávamos".

## Regra

**Hipótese se registra ANTES de rodar.** Critério de sucesso fixado antes de ver o
dado. "Inconclusivo" é resultado válido e encerra a hipótese sem repescagem de
parâmetros. Ajustar parâmetros após ver o resultado = nova hipótese, novo registro,
nova janela.

## Formato

```
### H<N> — <nome curto>            (status: registrada | rodando | confirmada | refutada)
- Data do registro:
- Hipótese (mecanismo causal, 1-2 frases):
- Configuração (entra no TrialRegistry como `name`):
- Critério de sucesso (definido ANTES — métrica, limiar, IC, líquido de custos):
- Janela de dados (treino/teste, sem sobreposição):
- Resultado (preenchido DEPOIS):
```

## Registro

### H0 — exemplo (status: registrada)
- Data do registro: AAAA-MM-DD
- Hipótese: <mecanismo causal>.
- Configuração: `<dominio>-<feature>-<horizonte>`.
- Critério de sucesso: <ex.: IC95 do ΔSharpe (bootstrap por bloco) exclui zero> —
  **líquido de custos**; e DSR ≥ 0,95 descontando as tentativas registradas.
- Janela: calibração até <data>; teste <data> → <data>.
- Resultado: (preencher após a rodada)
