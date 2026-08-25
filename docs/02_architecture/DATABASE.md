# Arquitetura de banco de dados

## Estratégia

SQLite é a persistência local prevista, acessada por implementações em
`src/nexo/infrastructure/database/`. SQLAlchemy ou mecanismo equivalente fica
restrito à Infrastructure. Modelos ORM são diferentes dos modelos em
`domain/models` e nunca são entregues diretamente à UI.

O banco persiste dados estruturais e fatos. `Transaction` é a fonte principal
de verdade financeira; `Position` e métricas consolidadas são reconstruídas.

## Schema conceitual inicial

### `portfolios`

| Campo | Finalidade |
|---|---|
| `id` | Identidade da carteira. |
| `name` | Nome fornecido pelo usuário. |

Restrições de nome e demais metadados devem ser definidos durante a
implementação, sem adicionar atributos antecipadamente.

### `transactions`

| Campo | Finalidade |
|---|---|
| `id` | Identidade da transação. |
| `portfolio_id` | Carteira à qual a operação pertence. |
| `asset_symbol` | Símbolo normalizado do ativo. |
| `transaction_type` | `BUY` ou `SELL`. |
| `quantity` | Quantidade positiva, preservada como decimal. |
| `unit_price` | Preço unitário positivo, preservado como decimal. |
| `date` | Data da operação. |

A chave estrangeira para `portfolios` garante que históricos permaneçam
separados. Precisão, escalas, índices e nomes físicos finais devem ser definidos
e testados junto da primeira implementação.

### `price_alerts`

Tabela prevista somente quando alertas forem implementados. Deve guardar a
carteira ou o contexto necessário, símbolo, condição e valor-alvo, conforme o
caso de uso confirmado.

## Dados não persistidos como estado financeiro

Não existe tabela `positions` como fonte de verdade. Também não se persistem
como estado independente quantidade consolidada, preço médio, valor investido,
lucro/prejuízo ou rentabilidade. Esses resultados são derivados das transações.

Uma tabela própria de ativos só se justifica se metadados ou ciclo de vida
independente surgirem. Não é necessária apenas para classificar símbolos.

## Modelos e repositórios

```text
domain/models/Portfolio       != infrastructure/database/models/PortfolioModel
domain/models/Transaction     != infrastructure/database/models/TransactionModel
```

Os modelos de domínio expressam regras; os modelos ORM expressam schema e
mapeamento. Repositórios concretos convertem entre eles e não vazam sessões ou
linhas ORM.

Contratos conceituais necessários incluem `PortfolioRepository` e
`TransactionRepository`, com implementações SQLAlchemy na Infrastructure.
`TransactionRepository` consulta por `portfolio_id`. Não se cria
`PositionRepository`.

## Transações, falhas e evolução

- escritas relacionadas devem ser atômicas e realizar rollback em erro;
- sessões não permanecem presas a widgets;
- a Application não executa SQL;
- testes usam banco isolado e verificam preservação de `Decimal` e datas;
- migrations só são criadas quando houver schema implementado e necessidade de
  evolução; bancos existentes não devem ser apagados silenciosamente.

O `.env.example` atualmente define
`NEXO_DATABASE_URL=sqlite:///data/nexo.db`, portanto `data/` é o local previsto
para o banco local. O arquivo gerado não deve ser versionado nem conter dados
sensíveis.

## Ambiguidade atual

`infrastructure/database/` já concentra migrations, modelos e repositórios,
enquanto `infrastructure/persistence/` também existe. Como ainda não há código
que delimite a segunda pasta, sua responsabilidade permanece indefinida; não se
deve duplicar persistência entre ambas.

Veja a decisão completa em
[`ADR-001`](decisions/ADR-001-transaction-ledger.md).
