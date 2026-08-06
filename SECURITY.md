# Security Policy

## Supported Versions

O projeto está em desenvolvimento ativo. Correções de segurança são aplicadas
na branch `main` e na release estável mais recente.

| Versão | Suporte |
|---|---|
| `main` | ✅ |
| release mais recente | ✅ |
| versões anteriores | ❌ |

## Reporting a Vulnerability

Não abra uma issue pública para relatar vulnerabilidades.

Use o recurso **Private vulnerability reporting** disponível na aba **Security**
deste repositório.

Inclua, quando possível:

- descrição clara do problema;
- módulo, contrato ou arquivo afetado;
- passos mínimos para reprodução;
- impacto esperado;
- versão do pacote e versão do Python;
- evidências sanitizadas;
- possível correção ou mitigação.

Não publique segredos, tokens, credenciais, datasets privados, artefatos de
produção ou dados obtidos durante os testes.

## Security Scope

Estão dentro do escopo:

- contratos públicos e validação de dados;
- serialização, desserialização e parsing;
- ingestão e transformação de dados;
- clientes HTTP e scraping opcionais;
- prevenção de lookahead e integridade temporal;
- métricas, trials e artefatos científicos;
- compatibilidade e estabilidade da API pública;
- instalação e importação do wheel fora do checkout;
- dependências Python e extras opcionais;
- workflows do GitHub Actions;
- cadeia de fornecimento e artefatos de release;
- exposição acidental de segredos em código, testes ou logs.

Não estão dentro do escopo:

- indisponibilidade de fontes externas;
- resultados científicos incorretos causados por dados de entrada inválidos já
  rejeitados pelo contrato documentado;
- engenharia social;
- ataques que dependam de credenciais comprometidas fora do projeto;
- vulnerabilidades já corrigidas na branch `main`;
- falhas exclusivamente em versões antigas de dependências.

## Secrets and Sensitive Data

Nunca faça commit de:

- arquivos `.env`;
- tokens de API;
- senhas ou chaves privadas;
- credenciais de provedores de dados;
- datasets privados ou licenciados;
- artefatos contendo dados pessoais;
- logs não sanitizados;
- credenciais usadas por consumidores do pacote.

Caso um segredo seja exposto, removê-lo do código não é suficiente. Ele deve ser
revogado ou rotacionado imediatamente no provedor correspondente.

## Safe Testing

Durante testes de segurança:

- utilize somente ambientes e dados sob seu controle;
- utilize credenciais e datasets fictícios;
- não ataque serviços ou fontes de terceiros;
- não provoque indisponibilidade deliberada;
- não preserve dados obtidos durante a investigação;
- não execute alterações em repositórios consumidores;
- pare o teste assim que houver evidência suficiente.

## Response Process

Após o recebimento de um relatório:

1. o problema será analisado;
2. impacto, alcance e severidade serão avaliados;
3. uma correção será preparada quando necessária;
4. segredos comprometidos deverão ser rotacionados;
5. testes de regressão serão adicionados quando aplicável;
6. uma nova versão poderá ser publicada;
7. a divulgação pública ocorrerá somente após a correção.

Não há garantia de prazo fixo de resposta, pois este é um projeto pessoal
mantido individualmente.
