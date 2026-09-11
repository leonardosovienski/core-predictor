# HANDOFF — predictor-core

## Entrega arquitetural publicada — 11/09/2026

Versão **3.2.1** publicada: [release e artefatos](https://github.com/leonardosovienski/core-predictor/releases/tag/v3.2.1). [CI de engenharia aprovada](https://github.com/leonardosovienski/core-predictor/actions/runs/34627786114) para a fonte `7bb212cfa06333886e11e849b209c5aab801c04b`. Consulte [ARCHITECTURE_IMPLEMENTATION.md](ARCHITECTURE_IMPLEMENTATION.md) para comportamento, migração e limites. Este registro atualiza a entrega de software; estados científicos e registros datados abaixo conservam sua autoridade e contexto histórico.

**Estado corrente: 2026-09-02 — versão 3.1.0.**

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


## Implementação arquitetural local — 2026-09-11

As alterações candidatas, seus limites, verificações e rollback estão em [ARCHITECTURE_IMPLEMENTATION.md](ARCHITECTURE_IMPLEMENTATION.md). Esta implementação local não publica releases, não atualiza automaticamente os consumidores e não altera os vereditos científicos históricos.
