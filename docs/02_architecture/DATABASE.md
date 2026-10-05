# Arquitetura de banco de dados

## Implementação atual — incremento 01

A persistência SQL fica oficialmente em
`src/nexo/infrastructure/database/`. SQLite é acessado por SQLAlchemy >=2.0.
`infrastructure/persistence/` permanece vazio e não recebe implementação SQL.

```text
database/
├── session.py
├── models/portfolio_model.py
└── repositories/portfolio_repository.py
```

`Portfolio` não é um modelo ORM. `SqlAlchemyPortfolioRepository` implementa
`PortfolioRepository`, converte ORM em entidades e não entrega sessões/modelos
SQLAlchemy à Application ou UI.

## Caminho e inicialização

`default_database_path()` resolve `<raiz do checkout>/data/nexo.db` pelo
local de `session.py`. Iniciar de outra pasta não altera o banco escolhido.
Esse caminho atende a execução no checkout instalado em modo editável.

`create_database_engine()` cria o diretório. `initialize_database()` executa
explicitamente `Base.metadata.create_all(engine)`, sem apagar dados existentes.
Não há Alembic ou migração de schema neste incremento.

O `.env`/`NEXO_DATABASE_URL` não é consumido nesta etapa. O caminho opcional
recebido pela composição/infraestrutura permite diagnósticos e testes isolados.
O arquivo padrão e outros bancos gerados são ignorados pelo Git.

## Schema real

A única tabela implementada é `portfolios`:

| Campo | Tipo SQLite | Restrição |
|---|---|---|
| `id` | `INTEGER` | Chave primária gerada pelo banco |
| `name` | `TEXT` | `NOT NULL`; não é único |

O Domain remove espaços nas extremidades e rejeita nome vazio. Nomes iguais
representam carteiras distintas quando os IDs diferem. Não há campos
financeiros, estratégias, descrições, usuários ou outras tabelas.

## Operações, sessões e falhas

- `add()` aceita uma entidade nova, faz flush, obtém o ID e retorna uma nova
  entidade somente depois de o commit concluir;
- a entidade original não é modificada;
- cada gravação usa `session_factory.begin()`, com rollback em erro;
- `list_all()` usa sessão própria e ordena por ID;
- exceções SQLAlchemy são traduzidas em `PortfolioRepositoryError`;
- a UI conserva a entrada e não cria cards em falha de gravação;
- falha de leitura conserva cards existentes e permite atualizar novamente.

## Evolução planejada, ainda não implementada

`Transaction` será o ledger financeiro ligado a uma carteira. O schema futuro
pode conter `id`, `portfolio_id`, `asset_symbol`, `transaction_type`, `quantity`,
`unit_price` e `date`; tipos finais, ordenação e precisão serão definidos junto
das regras. Nenhuma tabela de transações foi antecipada.

`Position` e métricas serão reconstruídas, sem tabela/repositório próprio
inicialmente. `Asset` não exige tabela apenas para identificar símbolos.
Alertas/configurações só receberão schema quando seus casos de uso existirem.

Testes de integração verificam schema, mapeamento, nomes duplicados,
reabertura e rollback em SQLite temporário. Nunca usam `data/nexo.db`.

Referência: [`ADR-001`](decisions/ADR-001-transaction-ledger.md).
