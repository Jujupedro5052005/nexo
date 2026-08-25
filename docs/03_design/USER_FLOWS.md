# Fluxos do usuário

Os fluxos descrevem comportamento observável e pontos de coordenação, sem
duplicar detalhes internos dos documentos de arquitetura.

## Criar carteira

```text
Usuário informa nome
  → UI
  → CreatePortfolio
  → PortfolioRepository
  → SQLite
  → carteira selecionável na UI
```

Uma carteira vazia continua existindo porque `id` e `name` são persistidos.

## Registrar compra

```text
UI
  → RegisterPurchase
  → validação
  → TransactionRepository
  → SQLite
  → LoadPortfolio
  → reconstrução de Positions
  → UI atualizada
```

A transação sempre recebe a carteira selecionada. A UI não altera posição
diretamente.

## Registrar venda

```text
UI
  → RegisterSale
  → LoadPortfolio
  → verificar quantidade disponível
  → TransactionRepository
  → SQLite
  → reconstrução do Portfolio
  → UI atualizada
```

Venda acima do saldo é rejeitada sem persistência parcial e com mensagem clara.

## Consultar mercado

```text
UI
  → Application
  → MarketDataProvider
  → adaptador externo
  → API financeira
  → Application
  → UI
```

Carregamento e indisponibilidade devem ser visíveis. A UI não faz HTTP.

## Comparar carteiras

```text
UI seleciona carteiras
  → ComparePortfolios
  → carregar carteiras e transações
  → reconstruir posições
  → calcular métricas
  → resultado comparativo
  → UI
```

As métricas comparáveis precisam indicar período, moeda e dependência de
cotação quando aplicável.

## Configurar alerta

```text
UI informa ativo, condição e valor
  → caso de uso de alerta
  → validação
  → persistência de PriceAlert
  → confirmação na UI
```

A exibição dentro do aplicativo pode vir primeiro. Canais externos são futuros.
