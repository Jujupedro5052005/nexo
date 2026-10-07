# Arquitetura de software do Nexo Invest

## Composição atual — 05.2

`main.py` injeta contratos separados de mercado, fundamentos, dividendos e dados
oficiais. ProviderServices gerencia composição/lifecycle; não é um provider
universal. ProviderPolicy compartilha TTL/coalescing/health; ProviderUsage reserva
operações remotas com persistência local sem segredos. brapi, bolsai, Yahoo e CVM
ficam exclusivamente em Infrastructure. Ledger/schema permanecem independentes.
As seções 01–05 abaixo registram a evolução histórica; composição real e routing
atual estão em [DATA_PROVIDERS.md](DATA_PROVIDERS.md).

## Visão geral

O Nexo Invest adota uma separação prática compatível com a árvore atual. Não se
pretende implementar Clean Architecture formal nem abstrações sem caso real.

```text
UI
 ↓
Application
 ↓
Domain

Calculations fornece cálculos financeiros reutilizáveis.
Infrastructure implementa persistência e integrações externas.
main.py compõe as dependências concretas.
```

## Mapeamento para o repositório

| Parte | Caminho | Responsabilidade |
|---|---|---|
| UI | `src/nexo/ui/` | Interface PySide6, apresentação e interação. |
| Application | `src/nexo/application/` | Casos de uso e coordenação. |
| Domain | `src/nexo/domain/` | Conceitos centrais, invariantes e contratos. |
| Calculations | `src/nexo/calculations/` | Indicadores, projeções, risco e valuation. |
| Infrastructure | `src/nexo/infrastructure/` | Banco, APIs de mercado e notificações. |
| Composition root | `src/nexo/main.py` | Instancia e conecta as partes. |
| Core | `src/nexo/core/` | Pasta existente; responsabilidade ainda não definida. |

Diretórios com apenas `.gitkeep` representam estrutura preparada, não
funcionalidade implementada.

## Fluxo implementado no incremento 01

`Portfolio` contém somente nome validado e identidade inteira opcional.
`CreatePortfolio` e `ListPortfolios` usam a ABC `PortfolioRepository` de
`domain/interfaces`. `SqlAlchemyPortfolioRepository` implementa esse contrato,
com sessões por operação e conversão para entidades. `main.py` inicializa o
schema e injeta os casos de uso na `MainWindow`.

O incremento 03 amplia o fluxo real para Movimentações, posições e resumos de
Carteiras/Visão Geral. A seleção por ID vive na janela durante a sessão;
recursos complementares permanecem demonstrativos; mercado real foi entregue no 04.

## Responsabilidades

### UI

`ui/` contém `components`, `controllers`, `dialogs`, `pages`, `resources`,
`styles`, `viewmodels`, `widgets` e `windows`. É uma separação prática, sem
impor MVC ou MVVM rígido. A UI não executa SQL, não conhece modelos ORM, não
chama APIs diretamente e não calcula preço médio ou posições.

### Application

`application/` está organizada em `alerts`, `analysis`, `assets`, `education`,
`financial_planning` e `portfolio`. Coordena domínio, cálculos, repositórios e
serviços por contratos simples. Operações conceituais incluem
`CreatePortfolio`, `UpdatePortfolio`, `DeletePortfolio`, `RegisterPurchase`,
`RegisterSale`, `LoadPortfolio`, `ComparePortfolios` e `LoadDashboard`, sem
obrigar uma classe por nome. Não implementa UI nem executa SQL ou HTTP direto.

### Domain

`domain/` contém `models`, `enums`, `interfaces` e `services`. Seus conceitos
principais são `Asset`, `Portfolio`, `Position`, `Transaction`,
`TransactionType` e `PriceAlert`. Protege invariantes e não depende de PySide6,
SQLAlchemy, SQLite ou formatos de APIs. Serviços de domínio só entram quando
uma regra não pertencer naturalmente a um modelo.

### Calculations

`calculations/` concentra cálculos reutilizáveis em `indicators`,
`projections`, `risk` e `valuation`. Deve ser independente da UI e, sempre que
possível, da Infrastructure. Cálculos não são duplicados em telas ou casos de
uso.

### Infrastructure

- `database/models`: modelos do ORM, distintos dos modelos do domínio;
- `database/repositories`: implementações concretas;
- `database/migrations`: evolução do schema quando necessária;
- `market_data/adapters`: adaptadores de provedores financeiros;
- `notifications`: integrações futuras;
- `persistence`: pasta vazia; persistência SQL fica oficialmente em `database/`.

Não existe `PositionRepository`, pois `Position` é reconstruída.

## Regras de dependência

| Origem | Pode usar | Não pode usar diretamente |
|---|---|---|
| Domain | biblioteca padrão e módulos próprios | PySide6, SQLAlchemy, SQLite, HTTP, UI |
| Calculations | tipos simples e Domain quando necessário | widgets, banco, HTTP |
| Application | Domain, Calculations e contratos | PySide6, SQL, ORM, detalhes HTTP |
| Infrastructure | contratos internos, Domain e bibliotecas técnicas | widgets e páginas |
| UI | Application e modelos de apresentação | banco, ORM, HTTP e regras financeiras |
| `main.py` | todas as partes para composição | regras de negócio |

Objetos PySide6 e ORM não atravessam as fronteiras para o domínio.

## Persistência e reconstrução

O sistema suporta múltiplas carteiras. `Portfolio` tem `id` e `name`
persistidos. `Transaction` é a fonte principal de verdade financeira e pertence
a uma carteira. `Position`, preço médio, valor investido, lucro/prejuízo e
rentabilidade são derivados.

```text
Portfolio selecionado
        ↓
TransactionRepository
        ↓
transações da carteira
        ↓
LoadPortfolio
        ↓
Portfolio com Positions reconstruídas
```

Detalhes: [`ADR-001`](decisions/ADR-001-transaction-ledger.md),
[`DOMAIN_MODEL.md`](DOMAIN_MODEL.md) e [`DATABASE.md`](DATABASE.md).

## Polimorfismo e herança

Polimorfismo pode surgir em componentes intercambiáveis, como
`MarketDataProvider` e seus adaptadores ou implementações de repositório. O
contrato pode usar `Protocol`, interface simples, abstração ou duck typing; a
estratégia não é imposta antes da implementação.

Herança não é requisito arquitetural. `Asset` não possui subclasses por tipo
de investimento. Só haverá hierarquia diante de especialização real, com
diferenças concretas de estado ou comportamento.

## Limites

Não estão previstos CQRS, event sourcing, eventos de domínio, message bus,
microserviços, DDD completo, service locator ou framework de injeção de
dependência. Repositórios, serviços e interfaces não serão criados
automaticamente para cada classe.

Erros de formato pertencem à UI, invariantes ao Domain, coordenação à
Application e falhas técnicas à Infrastructure. Escritas devem evitar estado
parcial; detalhes SQL e credenciais nunca chegam ao usuário.

## Fluxo histórico implementado no incremento 02

Asset, Transaction e Position imutáveis estão em domain/models; TransactionType
(BUY/SELL) em domain/enums. domain/reconstruction.py concentra replay por
(portfolio_id, Asset), valida saldo e produz resultado imutável com abertas e
encerradas separadas. Regras de custo médio, taxas, zeragem, recompra, ordenação
e precisão estão em [DOMAIN_MODEL.md](DOMAIN_MODEL.md).

Reconstrução usa somente biblioteca padrão e domínio. Não exige nova Application,
repository ou integração ORM. Transaction permanece em memória; o diagrama de
TransactionRepository acima representa o fluxo futuro. Position não é persistida.

## Fluxo atual — Grande Incremento 03

main.py compõe engine/session factory, repositories de Portfolio e Transaction,
CreatePortfolio, ListPortfolios, RegisterTransaction, ListTransactions,
LoadPortfolioPositions e MainWindow. UI não importa SQLAlchemy nem executa SQL.
TransactionRepository é ABC mínima; implementação fica na Infrastructure.

RegisterTransaction valida replay completo antes de add. ListTransactions usa a
ordem oficial compartilhada com o replay. LoadPortfolioPositions reconstrói sem
persistir snapshots; seu método summary fornece métricas para cards. A Application
agrega custo/realizado preservando Decimal. Transaction.amounts centraliza
bruto/total líquido e taxas, utilizado também pela reconstrução e apresentação.

MainWindow.selected_portfolio_id coordena formulário, histórico, posições e
resumos. Registro bem-sucedido atualiza imediatamente as três páginas; troca de
carteira limpa dados antigos inclusive quando a leitura falha. Cards financeiros
usam custo de aquisição, nunca uma cotação inventada. Demos são identificadas por
seção. Dependências opcionais da MainWindow preservam construção do shell em
testes antigos; main.py sempre injeta todos os casos de uso reais.

Detalhes de TEXT Decimal, ISO datetime, IDs crescentes, FK e limitação de
concorrência: [DATABASE.md](DATABASE.md). As seções dos incrementos 01/02 acima
registram sua entrega histórica; o fluxo atual inclui persistência e UI.


## Fluxo atual — Grande Incremento 04

main.py também compõe MarketSettings, BrapiMarketDataProvider, GetAssetQuote,
SearchAssets, GetAssetHistory e LoadPortfolioValuation. HTTP/JSON/autenticação
ficam na Infrastructure; Application depende da ABC MarketDataProvider no Domain.
calculations/valuation combina Position reconstruída e Quote com Decimal,
produzindo ValuedPosition/PortfolioValuation sem HTTP, SQL ou Qt.

MainWindow e AssetsPage delegam casos de uso a TaskRunner (QRunnable/QThreadPool).
Sinais enfileirados entregam resultado na thread GUI, com gerações por contexto
para descartar respostas atrasadas. Workers nunca acessam widgets. Sessões de
banco continuam locais a cada operação. Encerramento espera workers antes de
fechar provider/engine. Não há cache ou persistência de preços; refresh manual.

Ledger permanece independente de mercado. Valuation agrega somente quando todas
as posições podem ser expressas em BRL; ausências/moedas estrangeiras preservam
linhas e métricas locais, mas tornam agregado de mercado indisponível. Gráficos
Qt recebem float somente nas coordenadas, depois dos cálculos financeiros.

Contrato, endpoints, fórmulas e limites: [API_ARCHITECTURE.md](API_ARCHITECTURE.md).

## Fluxo atual — Grande Incremento 05

As seções 01–04 registram entregas anteriores. main.py agora compõe um único
BrapiMarketDataProvider/httpx.Client com CachedMarketDataProvider compartilhado.
FundamentalDataProvider permanece ABC separada. AnalyzeAsset coordena os dois
contratos e calculations de indicadores/valuation/risco; ComparePortfolios usa
ListPortfolios/ListTransactions/LoadPortfolioValuation, com IDs e batch existentes.
UI só apresenta os DTOs imutáveis; não conhece payload, HTTP ou SQL.

CompanyFundamentals/CashDividend/DividendSummary são snapshots externos, sem
alterar Transaction/Position nem schema. Concentração é propriedade derivada de
PortfolioValuation. Cache TTL em infraestrutura não é fonte financeira persistida.
Qt preserva gerações, callbacks na GUI e encerramento coordenado. Não há serviço
analítico genérico, tabela/repository de Position ou subclasses por categoria.

Fórmulas, unidades, proventos, cache e desenho futuro TWR:
[ANALYTICS.md](ANALYTICS.md).
