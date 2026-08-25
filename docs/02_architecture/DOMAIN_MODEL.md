# Modelo de domínio do Nexo Invest

## Princípio central

O sistema suporta múltiplas carteiras simuladas. Cada `Portfolio` possui
identidade e dados estruturais persistidos; seu estado financeiro é reconstruído
a partir do histórico de `Transaction`.

```text
Portfolio
├── id
├── name
├── Transaction history
└── derived Positions
    └── cada Position contém um Asset

Transaction contém o Asset negociado.
PriceAlert contém o Asset e a condição configurada.
```

O relacionamento interno enfatizado é composição. Não há hierarquia de
subclasses de ativos.

## `Asset`

Objeto de valor identificado por `symbol`, como `PETR4`, `VALE3`, `HGLG11` ou
`IVVB11`. O símbolo é normalizado e validado, e determina igualdade. Categoria
ou metadados podem surgir por requisito real, mas não existem subclasses
específicas por categoria na arquitetura atual.

## `Portfolio`

Entidade que representa uma carteira criada pelo usuário:

```text
Portfolio
├── id       (persistido)
├── name     (persistido)
└── positions (estado derivado)
```

Uma carteira pode existir sem transações. O sistema mantém históricos e
resultados separados para permitir estratégias e comparações. O comportamento
inclui reconstruir posições, validar vendas e produzir resumos coerentes.

## `Transaction`

Registra uma compra ou venda simulada e é a fonte principal de verdade
financeira. Campos conceituais: `id`, `portfolio_id`, `asset`,
`transaction_type`, `quantity`, `unit_price` e `date`.

`TransactionType` representa `BUY` ou `SELL`. Não são necessárias subclasses de
compra e venda. Quantidade e preço devem ser positivos; carteira e ativo devem
ser válidos; uma venda não pode exceder a quantidade reconstruída. Valores
monetários usam `Decimal`, nunca `float`.

## `Position`

Estado consolidado de um ativo na carteira. É uma projeção reconstruída, não
uma fonte de verdade e não possui tabela própria inicialmente. Pode conter
`asset`, `quantity`, `average_price`, `invested_value`, `current_value`,
`profit_loss` e `return_percentage`; os três últimos dependem de dados de
mercado.

Uma compra ou venda acrescenta uma transação ao ledger, não altera diretamente
uma posição persistida. Compras recalculam preço médio; vendas validam saldo e
aplicam a regra de custo definida e testada.

## `PriceAlert`

Representa uma condição configurada, como `PETR4 <= 30.00`. Pode ser persistido
quando implementado. A primeira entrega pode exibir alertas no aplicativo;
notificações externas são extensões futuras.

## Classificação e persistência

| Objeto | Papel | Persistência inicial |
|---|---|---|
| `Portfolio` | Entidade com identidade e nome | Estrutura persistida |
| `Transaction` | Entidade histórica do ledger | Persistida e vinculada à carteira |
| `Asset` | Objeto de valor pelo símbolo | Incorporado aos dados necessários; tabela própria não obrigatória |
| `Position` | Estado/projeção calculada | Não persistida |
| `PriceAlert` | Configuração do usuário | Pode ser persistida quando implementada |

## Serviços, contratos e precisão

Comportamentos permanecem nos objetos quando natural. `domain/services` é
reservado a regras que não pertençam a um único modelo; `domain/interfaces`
abriga somente contratos necessários. Não se cria uma interface ou serviço por
classe apenas para demonstrar POO.

Polimorfismo é mais adequado nas bordas intercambiáveis. Herança só será usada
diante de especialização real. Valores monetários usam `Decimal`; precisão e
arredondamento devem ser explícitos e testados.

Referências: [`ADR-001`](decisions/ADR-001-transaction-ledger.md),
[`DATABASE.md`](DATABASE.md) e
[`USER_FLOWS.md`](../03_design/USER_FLOWS.md).
