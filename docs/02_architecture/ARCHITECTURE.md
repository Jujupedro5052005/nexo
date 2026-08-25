# Arquitetura de software do Nexo

## 1. Decisão arquitetural

O Nexo terá quatro **áreas lógicas**: UI, Application, Domain e
Infrastructure. A separação é adequada porque protege regras financeiras de
PySide6/SQLAlchemy e torna o projeto testável e fácil de explicar. Ela não será
tratada como Clean Architecture completa: não haverá uma camada por operação,
event bus, command bus, unit of work genérica, factories universais ou DTO para
cada método interno.

```text
Usuário
  |
  v
UI (PySide6) ---> Application (casos de uso) ---> Domain (regras e objetos)
                         |
                         v contrato
                  TransactionRepository
                         ^
                         |
Infrastructure (SQLAlchemy/SQLite)

main.py monta objetos concretos e injeta os casos de uso na UI.
```

As setas indicam dependência de código. Infrastructure conhece o contrato da
Application e os objetos do Domain para implementar persistência; Domain não
conhece nenhuma outra área.

## 2. Responsabilidades

### UI

- criar janelas, páginas, formulários, tabelas e gráfico com PySide6;
- coletar entrada e fazer validação de apresentação/formato;
- chamar casos de uso com tipos Python, nunca com widgets;
- exibir DTOs/resultados e mensagens seguras;
- disparar recarga das páginas após uma operação bem-sucedida.

A UI não calcula preço médio, não valida saldo da posição, não usa sessão
SQLAlchemy e não faz HTTP.

### Application

- representar as ações completas do usuário;
- coordenar repositório e objetos de domínio;
- definir comandos/resultados simples, preferencialmente `dataclass`;
- demarcar o comportamento atômico de cada operação;
- traduzir falhas técnicas em erros de aplicação apresentáveis.

Casos de uso iniciais:

- `RegisterPurchase`;
- `RegisterSale`;
- `LoadPortfolio` (posições e histórico);
- `LoadDashboard`.

Não haverá uma classe `Service` genérica. Cada caso de uso tem nome e objetivo
explícitos.

### Domain

- representar transações, ativos, posições e a visão da carteira;
- proteger invariantes de quantidade, preço, código do ativo e venda;
- derivar posições e preço médio do histórico;
- calcular custo total e alocação por custo;
- permanecer Python puro, sem PySide6, SQLAlchemy, SQLite ou HTTP.

### Infrastructure

- configurar engine, sessão e schema SQLAlchemy;
- mapear linhas ORM para objetos do domínio e vice-versa;
- implementar `TransactionRepository` com SQLite;
- controlar commit/rollback dentro de cada método de escrita;
- traduzir exceções SQLAlchemy em falhas de persistência conhecidas pela
  Application;
- no futuro, conter o adaptador da API de mercado.

## 3. Regras de dependência

| Origem | Pode depender de | Não pode depender de |
|---|---|---|
| Domain | biblioteca padrão | Application, Infrastructure, PySide6, SQLAlchemy, HTTP |
| Application | Domain e seu contrato mínimo de repositório | PySide6, modelos ORM, engine/sessão, cliente HTTP |
| Infrastructure | Domain, contrato da Application, SQLAlchemy/SQLite | widgets ou páginas da UI |
| UI | Application e DTOs de saída | SQLAlchemy, SQLite, HTTP e regras internas do Domain |
| `main.py` | todas as áreas para montagem | regras de negócio |

Importações circulares são proibidas. A UI não recebe o repositório; recebe
casos de uso já construídos. O domínio nunca retorna objetos PySide6 ou ORM.

## 4. Principais classes do CORE

| Área | Classe | Papel |
|---|---|---|
| Domain | `Asset` | Objeto imutável que normaliza e valida o código do ativo. |
| Domain | `Transaction` | Entidade imutável identificada que registra compra ou venda. |
| Domain | `TransactionType` | Enum `BUY`/`SELL`; evita subclasses artificiais. |
| Domain | `Position` | Resultado imutável e calculado de quantidade, preço médio e custo de um ativo. |
| Domain | `Portfolio` | Objeto de domínio transitório construído do histórico; valida operações e deriva posições/resumos. Não é entidade persistida. |
| Application | `RegisterPurchase` | Valida/cria compra pelo domínio e solicita persistência. |
| Application | `RegisterSale` | Carrega histórico, valida disponibilidade e persiste venda. |
| Application | `LoadPortfolio` | Carrega histórico e devolve posições/histórico como DTOs. |
| Application | `LoadDashboard` | Carrega histórico e devolve custo total e fatias de alocação. |
| Application | `TransactionRepository` | Único contrato de persistência necessário no CORE. |
| Infrastructure | `TransactionModel` | Modelo ORM isolado do domínio. |
| Infrastructure | `SqlAlchemyTransactionRepository` | Implementação SQLite do contrato. |
| UI | `MainWindow` | Shell e navegação entre carteira, histórico e dashboard. |
| UI | `TransactionForm` | Formulário reutilizado para compra/venda. |
| UI | `PortfolioPage` | Posições, histórico e acionamento do formulário. |
| UI | `DashboardPage` | Resumo e gráfico de alocação. |

## 5. Abstração mínima de repositório

Um repositório é útil porque evita que casos de uso importem SQLAlchemy e
permite testar regras com uma implementação em memória. O contrato mínimo é
conceitualmente:

```text
TransactionRepository
  list_all() -> list[Transaction]
  add(transaction: Transaction) -> None
```

Não são necessários no CORE `AssetRepository`, `PositionRepository`,
`PortfolioRepository`, repositório base genérico, Unit of Work ou padrão
Specification. Consultas adicionais só entram quando um caso de uso real exigir
desempenho ou filtragem.

O contrato pode ser um `Protocol`, evitando herança obrigatória. O polimorfismo
surge naturalmente: casos de uso operam tanto com o repositório SQLAlchemy
quanto com um repositório em memória nos testes.

## 6. Validações e erros entre áreas

| Tipo | Onde nasce | Exemplo | Como atravessa |
|---|---|---|---|
| Formato/apresentação | UI | campo vazio, texto que não converte para decimal | UI marca o campo; caso de uso não é chamado |
| Regra de domínio | Domain | quantidade/preço não positivos, ticker inválido, venda sem saldo | Exceção específica derivada de `DomainError`; Application preserva; UI converte em mensagem clara |
| Coordenação/aplicação | Application | operação não concluída por falha de persistência | `ApplicationError` com mensagem segura e causa técnica encadeada |
| Técnica | Infrastructure | erro SQLite/SQLAlchemy | rollback, registro técnico e tradução; nunca exibir SQL ao usuário |

Erros esperados não usam booleanos ambíguos nem caixas de diálogo dentro do
domínio. Uma falha não pode gerar gravação parcial. A UI captura apenas a base
de erros esperados; erros inesperados recebem mensagem genérica e são
registrados para diagnóstico.

## 7. Fluxos completos

### Compra

1. `TransactionForm` valida presença e formato e cria `PurchaseCommand`.
2. A UI chama `RegisterPurchase.execute(command)`.
3. O caso de uso cria `Asset` e `Transaction(BUY)`; o Domain valida invariantes.
4. `TransactionRepository.add()` persiste uma única transação e confirma a
   sessão; em erro, faz rollback.
5. O caso de uso retorna um resultado simples com ID e mensagem de sucesso.
6. A UI limpa/fecha o formulário e chama `LoadPortfolio` e `LoadDashboard` para
   atualizar as telas.

Para compra não é necessário carregar toda a carteira, pois quantidade e preço
positivos já garantem a validade local da nova transação.

### Venda

1. `TransactionForm` cria `SaleCommand` após validar formato.
2. A UI chama `RegisterSale.execute(command)`.
3. O caso de uso cria `Transaction(SELL)`, chama `repository.list_all()` e
   constrói `Portfolio`.
4. `Portfolio` simula a aplicação da nova transação na ordem cronológica e
   verifica a quantidade disponível do ativo naquele ponto do histórico.
5. Se insuficiente, lança erro de domínio e nada é gravado.
6. Se válida, o caso de uso chama `add()` para persistir a venda.
7. Após commit, a UI recarrega carteira e dashboard.

### Dashboard

1. A página chama `LoadDashboard.execute()` ao abrir ou após transação.
2. O caso de uso carrega transações e cria `Portfolio`.
3. O Domain deriva posições, custo total e alocação por custo.
4. O caso de uso converte o resultado em `DashboardDTO` com valores e fatias.
5. `DashboardPage` renderiza cards e gráfico; ela não refaz cálculos.
6. Sem posições, a página exibe estado vazio válido, não um erro.

## 8. Organização inicial de `src/nexo`

```text
src/nexo/
├── main.py                         # composition root e início da aplicação
├── domain/
│   ├── asset.py
│   ├── transaction.py
│   ├── position.py
│   ├── portfolio.py
│   └── errors.py
├── application/
│   ├── commands.py                 # PurchaseCommand e SaleCommand
│   ├── dto.py                      # resultados para UI
│   ├── ports.py                    # TransactionRepository
│   ├── register_purchase.py
│   ├── register_sale.py
│   ├── load_portfolio.py
│   ├── load_dashboard.py
│   └── errors.py
├── infrastructure/
│   ├── database.py                 # engine, sessão, inicialização do schema
│   ├── models.py                   # TransactionModel
│   └── transaction_repository.py   # implementação SQLAlchemy
└── ui/
    ├── main_window.py
    ├── transaction_form.py
    ├── portfolio_page.py
    └── dashboard_page.py
```

Não serão criados diretórios `entities`, `value_objects`, `adapters`, `ports`,
`presenters` e `controllers` aninhados. Os quatro pacotes existentes bastam.
Os diretórios legados `core/` e `calculations/` não devem receber lógica nova;
uma decisão de remoção pode ser tomada separadamente quando estiverem vazios.

## 9. Conceitos de POO e evidência

| Conceito | Evidência natural |
|---|---|
| Classes e objetos | `Transaction`, `Asset`, `Portfolio`, `Position` e casos de uso. |
| Atributos e métodos | Estado imutável das transações e métodos de cálculo/validação do portfólio. |
| Encapsulamento | Objetos validam sua criação; `Portfolio` impede venda inválida e não expõe estado mutável. |
| Associação | `Transaction` referencia `Asset`; DTOs associam posições e histórico. |
| Composição | `Portfolio` é construído com transações e produz posições. |
| Abstração | `Asset` modela apenas o código relevante; `TransactionRepository` esconde persistência. |
| Polimorfismo | Mesmo contrato com implementação SQLAlchemy e implementação em memória para testes. |
| Herança | Não planejada no domínio; somente bases técnicas de exceção. Será usada apenas se surgir relação “é um” real. |
| Responsabilidade única | Cada área e caso de uso possui um motivo claro para mudar. |
| Modularização | Quatro pacotes com dependências explícitas e domínio isolado. |

## 10. Riscos de overengineering e limites

- não criar classe base para todas as entidades;
- não criar subclasses `Stock`, `FII` e `ETF` sem comportamento distinto;
- não criar subclasses `Purchase` e `Sale`; usar enum;
- não persistir `Position`, pois duplicaria uma projeção do histórico;
- não persistir `Portfolio` ou criar gestão de múltiplas carteiras no CORE;
- não criar controller ou ViewModel: casos de uso já são a fronteira da UI;
- não criar uma interface para cada classe ou serviço;
- não aplicar CQRS, event sourcing, mediator, service locator ou DI container;
- não introduzir Alembic enquanto o schema acadêmico inicial puder ser criado
  de forma determinística e ainda não houver migração de dados reais;
- não preparar abstrações para API antes do MVP EXTENDED.

## 11. Decisões difíceis de reverter

A escolha de transações como fonte de verdade e posições derivadas afeta
schema, regras e migrações, por isso está registrada em
`decisions/ADR-001-transaction-ledger.md`. As demais simplificações podem ser
revistas incrementalmente e não precisam de ADR agora.
