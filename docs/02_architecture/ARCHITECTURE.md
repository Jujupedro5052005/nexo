# Arquitetura de software do Nexo Invest

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
- `persistence`: pasta existente cuja fronteira com `database/` ainda precisa
  ser delimitada.

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
