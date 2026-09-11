# Implementação arquitetural — 2026-09-11

Release 3.2.1 publicada. A biblioteca conserva zero dependências obrigatórias e não exige instalação dos domínios, Ops, Ecosystem ou CAIN.

`LatencySLA` e `ResourceBudget` rejeitam NaN e infinitos em qualquer campo. As fachadas raiz e `contracts` resolvem seus símbolos públicos sob demanda; importar `contracts.scientific` não carrega rede, trials ou persistência. Novos consumidores devem usar caminhos explícitos, como `predictor_core.contracts.scientific` e `predictor_core.measurement.stats`. Todos os símbolos públicos anteriores foram preservados.

O grupo de desenvolvimento `architecture` contém import-linter; não é dependência de runtime. O contrato impede dependências de I/O, medição e harness no módulo de contratos científicos escalares. A CI passa a conferir essa fronteira.

Validação local: 278 testes, 86,33% de cobertura, Ruff, Pyright e contrato de imports aprovados. Nenhum atestado científico foi reemitido. Pins dos consumidores publicados não foram trocados por números de versões ainda não publicadas. Rollback é reinstalar o wheel anterior; não há migração de dados.

A CI e release passaram; a biblioteca mínima foi verificada isoladamente. Uma cópia sintética recebeu import proibido e o Import Linter recusou a dependência com exit 1, sem alterar a fonte publicada.

## Entrega arquitetural publicada — 11/09/2026

Versão **3.2.1** publicada: [release e artefatos](https://github.com/leonardosovienski/core-predictor/releases/tag/v3.2.1). [CI de engenharia aprovada](https://github.com/leonardosovienski/core-predictor/actions/runs/34627786114) para a fonte `7bb212cfa06333886e11e849b209c5aab801c04b`. Consulte [ARCHITECTURE_IMPLEMENTATION.md](ARCHITECTURE_IMPLEMENTATION.md) para comportamento, migração e limites. Este registro atualiza a entrega de software; estados científicos e registros datados abaixo conservam sua autoridade e contexto histórico.
