# Implementação arquitetural — 2026-09-11

Candidato 3.2.1. A biblioteca conserva zero dependências obrigatórias e não exige instalação dos domínios, Ops, Ecosystem ou CAIN.

`LatencySLA` e `ResourceBudget` rejeitam NaN e infinitos em qualquer campo. As fachadas raiz e `contracts` resolvem seus símbolos públicos sob demanda; importar `contracts.scientific` não carrega rede, trials ou persistência. Novos consumidores devem usar caminhos explícitos, como `predictor_core.contracts.scientific` e `predictor_core.measurement.stats`. Todos os símbolos públicos anteriores foram preservados.

O grupo de desenvolvimento `architecture` contém import-linter; não é dependência de runtime. O contrato impede dependências de I/O, medição e harness no módulo de contratos científicos escalares. A CI passa a conferir essa fronteira.

Validação local: 278 testes, 86,33% de cobertura, Ruff, Pyright e contrato de imports aprovados. Nenhum atestado científico foi reemitido. Pins dos consumidores publicados não foram trocados por números de versões ainda não publicadas. Rollback é reinstalar o wheel anterior; não há migração de dados.
