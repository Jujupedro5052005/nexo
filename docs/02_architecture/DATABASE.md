# Arquitetura de banco de dados

## Implementação atual — Grande Incremento 03

SQLite via SQLAlchemy em `src/nexo/infrastructure/database/`. Domain e
Application não importam ORM; UI acessa casos de uso. Modelos ORM são separados
das entidades. infrastructure/persistence permanece vazio.

## Caminho e compatibilidade

default_database_path resolve `<checkout>/data/nexo.db` sem depender do cwd.
create_database_engine cria o diretório e habilita PRAGMA foreign_keys=ON em
cada conexão. initialize_database usa o metadata compartilhado dos modelos e
create_all, adicionando transactions a bancos antigos sem alterar portfolios.
Não há Alembic. .env/NEXO_DATABASE_URL não são consumidos; testes usam bancos
temporários e nunca o banco do usuário.

## Schema real

```text
portfolios
    id INTEGER PRIMARY KEY
    name TEXT NOT NULL (nomes duplicados permitidos)

transactions
    id INTEGER PRIMARY KEY AUTOINCREMENT
    portfolio_id INTEGER NOT NULL REFERENCES portfolios(id)
    asset_symbol TEXT NOT NULL
    transaction_type TEXT NOT NULL
    quantity TEXT NOT NULL
    unit_price TEXT NOT NULL
    fees TEXT NOT NULL
    occurred_at TEXT NOT NULL
    INDEX ix_transactions_portfolio_id (portfolio_id)
```

SQLite mantém sqlite_sequence como detalhe interno do AUTOINCREMENT.
Não existem tabelas de Asset/Position ou colunas de quantidade atual, custo médio,
custo total e resultado realizado. Esses valores são reconstruídos do ledger.

## Decimal e datetime

quantity/unit_price/fees armazenam str(Decimal), sem passagem por float ou tipos
REAL/Numeric. A leitura reconstrói Decimal diretamente da string, preservando
valor, precisão e escala. Nenhum quantize é aplicado na persistência.

occurred_at armazena datetime.isoformat(), com microssegundos e offset quando
presentes. datetime.fromisoformat() mantém datas naive sem fuso e datas aware
com o offset/instante original. Nomes de zonas IANA não são persistidos;
o contrato atual exige datetime e preservação de instante/offset, não timezone
externo. O timezone do Windows não participa da conversão.

## Repository e ordenação

TransactionRepository expõe apenas add e list_by_portfolio. add rejeita ID
preexistente, converte entidade para ORM, faz flush, reconstrói entidade e retorna
somente após commit. list_by_portfolio retorna entidades, nunca ORM ou Row.
Falhas são traduzidas para TransactionRepositoryError.

A consulta restringe portfolio_id; ordenação final usa order_transactions no
domínio, pois ordenar TEXT ISO não compara corretamente offsets distintos.
Critério: instante/data, ID crescente e estabilidade de entrada. O AUTOINCREMENT
assegura que a nova operação validada sem ID, após as existentes no timestamp,
permaneça nessa posição quando receber ID persistido.

## Validação, atomicidade e limites

RegisterTransaction carrega o histórico e reconstrói histórico + candidato antes
do INSERT. Valida retroatividade integral, não somente saldo atual. Venda
inválida não chama add. O repository usa sessão por operação e begin: commit em
sucesso, rollback em falha, sem reutilizar sessões danificadas. FK impede órfãos
mesmo em acessos diretos ao repository. Não se usa INSERT provisório para validar.

A leitura de validação e a escrita são operações separadas. Suporte atual é
aplicativo local single-user com uma instância escritora; não oferece garantia
contra escritores/processos simultâneos alterando o ledger entre essas etapas.
Não foram introduzidos locks distribuídos, versionamento ou CQRS.

## Testes

Round-trip Domain/ORM/SQLite/ORM/Domain de Decimal, datetime, Enum e Asset;
FK em conexões reabertas; isolamento; ordenação aware; rollback após flush;
reabertura; upgrade de banco portfolios-only; fluxo PETR4 e venda inválida.
Referência: [ADR-001](decisions/ADR-001-transaction-ledger.md).
