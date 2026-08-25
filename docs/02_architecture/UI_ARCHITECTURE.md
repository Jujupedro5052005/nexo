# Arquitetura da interface do CORE MVP

## 1. Decisão

PySide6 implementará uma interface desktop com `MainWindow` e poucas páginas.
Não haverá camada própria de Controller ou ViewModel no CORE. Os casos de uso
da Application já formam a fronteira de ações e consultas; acrescentar outro
intermediário apenas repassaria chamadas.

## 2. Componentes

| Componente | Responsabilidade |
|---|---|
| `MainWindow` | Criar shell, navegação e manter referências das páginas. |
| `PortfolioPage` | Exibir posições e histórico; abrir formulário; solicitar recarga. |
| `TransactionForm` | Coletar compra/venda e emitir submissão ao caso de uso apropriado. |
| `DashboardPage` | Exibir custo total, estado vazio e gráfico de alocação. |

Pode haver widgets reutilizáveis quando repetição real surgir, mas não será
criada uma biblioteca interna antecipadamente.

## 3. Comunicação com Application

`main.py` constrói repositório e casos de uso e os injeta nas páginas ou na
`MainWindow`. A UI nunca instancia SQLAlchemy.

```text
evento PySide6
  -> handler curto na página/formulário
  -> Command com Decimal/datetime/str
  -> use_case.execute(command)
  -> DTO de saída
  -> atualizar widgets
```

Regras:

- sinais PySide6 não atravessam para Domain/Infrastructure;
- casos de uso não recebem `QLineEdit`, `QDateEdit` ou outro widget;
- DTOs não importam PySide6 nem SQLAlchemy;
- páginas não recalculam preço médio, posição ou alocação;
- após uma escrita bem-sucedida, a UI chama novamente as consultas; não mantém
  um segundo estado financeiro mutável.

## 4. Navegação mínima

- **Carteira**: posições e ações de compra/venda;
- **Histórico**: pode ser uma seção/aba da página Carteira, não precisa de
  página própria;
- **Dashboard**: custo total e gráfico de alocação.

Não haverá roteador, navegação profunda, múltiplas janelas independentes nem
sistema de plugins.

## 5. Validação e mensagens

1. UI valida obrigatoriedade e conversão de tipos.
2. Domain valida regras financeiras.
3. Campo inválido recebe indicação próxima e mensagem objetiva.
4. `DomainError` vira mensagem específica, como “Quantidade disponível
   insuficiente”.
5. `ApplicationError` vira mensagem operacional segura, como “Não foi possível
   salvar a transação”.
6. Detalhes SQL, stack traces e credenciais nunca aparecem em diálogo.

O formulário permanece aberto após erro e preserva os dados para correção. Em
sucesso, a UI confirma a operação e atualiza carteira/dashboard.

## 6. Atualização das telas

Sem event bus ou estado global:

- `TransactionForm` informa sucesso à `PortfolioPage` por retorno ou signal
  local;
- a página chama `LoadPortfolio`;
- `MainWindow`/página solicita `LoadDashboard` quando necessário;
- cada carregamento substitui a visualização com um snapshot novo.

Esse fluxo é suficiente para o volume do MVP e é fácil de demonstrar.

## 7. Testes da UI

- testes unitários concentram-se em Domain/Application;
- testes de widgets cobrem submissão, mensagens e estado vazio quando úteis;
- um roteiro manual no Windows cobre F-01 a F-04;
- casos de uso falsos podem ser injetados na UI; não é necessário banco real
  em cada teste de widget.

## 8. Decisões evitadas

- sem Controller separado;
- sem MVVM/ViewModel;
- sem framework de navegação;
- sem service locator ou container de injeção;
- sem acesso direto ao repositório;
- sem lógica financeira em slots/signals;
- sem threads no CORE, pois não há rede.

Se a API futura for adicionada, chamadas de rede não poderão bloquear a thread
da UI; a estratégia assíncrona será decidida apenas nessa fase.
