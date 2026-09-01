# HANDOFF — predictor-core

**Estado corrente: 2026-09-01 — versão 3.0.0.**

Biblioteca científica instalável, com source em `src/predictor_core/`, Python 3.13
como baseline e 3.14 experimental. Distribuição moderna é exclusivamente por wheel;
vendoring é legado e `sync_core.py --audit` é somente leitura.

O 3.0 foi deliberadamente estreitado para primitivas com consumidores cross-domain
comprovados: contratos científicos/temporais, dados, métricas, bootstrap, trials,
replay, avaliação prequential e utilitários de teste. Foram removidos os antigos
contratos econômicos, rating, calibration, ordinal, ledger, null-reference, as-of e
stress da linha 2.x.

Os gates econômicos atuais de Brasileirão, cripto e ações permanecem nos domínios.
Core não escolhe bet, trade, rebalanceamento, sizing ou permissão de capital. Uma
abstração econômica só deve voltar após separar a regra verdadeiramente comum das
semânticas locais de odds, funding e turnover.

Validação:

```bash
uv sync --frozen --group dev
uv run python -m pytest
uv run ruff check .
uv run pyright
uv build --wheel
```

Nenhum workflow deste projeto modifica, commita ou publica em repositórios
consumidores.
