# Arquitetura de banco de dados do CORE MVP

## 1. Decisão

SQLite armazena somente fatos necessários: as transações simuladas. SQLAlchemy
fica restrito a Infrastructure e seus modelos não são entidades do domínio.
Posições e resumos são recalculados em memória.

## 2. Schema inicial

### Tabela `transactions`

| Coluna | Tipo lógico | Restrições/finalidade |
|---|---|---|
| `id` | texto UUID | chave primária, não nulo |
| `transaction_type` | texto | `BUY` ou `SELL`, não nulo |
| `asset_symbol` | texto | código normalizado, não nulo |
| `quantity` | numeric(20, 8) | maior que zero, não nulo |
| `unit_price` | numeric(20, 4) | maior que zero, não nulo |
| `occurred_at` | datetime | data efetiva informada, não nulo |
| `created_at` | datetime | auditoria/desempate, não nulo |

Índices iniciais:

- índice por `occurred_at`/`created_at` para ordenação;
- índice por `asset_symbol` somente se consultas ou volume justificarem. Para o
  MVP, ele pode ser omitido até medição.

Constraints do banco reforçam tipo e valores positivos, mas não substituem as
regras do domínio. A regra de venda depende do histórico e é validada antes da
inserção.

## 3. Tabelas deliberadamente ausentes

- `portfolios`: há uma única carteira sem identidade própria;
- `assets`: no CORE, o símbolo na transação basta;
- `positions`: são projeções calculadas;
- `dashboard` ou `allocations`: são resultados calculados;
- tabelas de cotações: pertencem ao MVP EXTENDED, se cache persistente for
  necessário.

## 4. Isolamento do SQLAlchemy

`TransactionModel` é uma classe ORM em `infrastructure/models.py`. Ela não
herda nem substitui `domain.Transaction`.

`SqlAlchemyTransactionRepository` faz o mapeamento explícito:

```text
TransactionModel <-> Transaction + Asset
```

Somente Infrastructure importa `Session`, `Engine`, `DeclarativeBase` ou
modelos ORM. O repositório devolve objetos do domínio, nunca linhas/modelos ORM.
Isso mantém testes de regras independentes do banco.

## 5. Sessões, transações e falhas

- engine e `sessionmaker` são criados em `database.py`;
- cada `add()` abre/recebe uma sessão curta, adiciona, faz commit e fecha;
- qualquer exceção causa rollback antes da tradução para erro de persistência;
- `list_all()` devolve transações ordenadas deterministicamente;
- nenhuma sessão permanece presa a widgets;
- conexão e criação do schema acontecem na inicialização da aplicação.

Como cada operação do CORE grava uma única transação, uma Unit of Work pública
não agrega benefício. Se um caso de uso futuro precisar de várias gravações
atômicas, essa decisão poderá ser revista.

## 6. Inicialização e evolução

Para a primeira versão acadêmica, `metadata.create_all()` é suficiente em um
banco local novo. Alembic não entra antes de existir necessidade real de
migrar dados preservados. Mudanças de schema após uso real exigem decisão de
migração; apagar silenciosamente o banco não é aceitável.

Configuração:

- URL em variável de ambiente/configuração, com padrão local seguro;
- arquivo do banco dentro de `data/` e fora do versionamento;
- banco temporário isolado nos testes de integração;
- nenhuma credencial incorporada ao código.

## 7. Testes de persistência

- salvar e recuperar compra e venda preservando `Decimal` e datas;
- garantir ordenação determinística;
- garantir rollback quando a gravação falhar;
- reabrir o banco e reconstruir as mesmas posições;
- confirmar que a infraestrutura não devolve `TransactionModel` à aplicação.

A decisão de usar transações como fonte de verdade está em
`decisions/ADR-001-transaction-ledger.md`.
