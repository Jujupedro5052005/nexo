# Modelo de domínio do Nexo Invest

## Estado implementado — Grande Incremento 03

Portfolio permanece a entidade estrutural persistida do incremento 01, sem
campos financeiros: `id: int | None` e `name: str`. Nome recebe trim e não pode
ser vazio; IDs são inteiros positivos e nomes iguais são permitidos.
PortfolioRepository continua oferecendo somente add e list_all.

O incremento 02 implementou o núcleo em memória. O Grande Incremento 03
implementa Transaction persistente e compra/venda pela UI, antecipando o fluxo
anteriormente previsto para o incremento 04. Domain permanece independente do ORM.

```text
Portfolio (id, name; persistido)
    ^ portfolio_id
Transaction (entidade imutável; ledger persistido via repository)
    | contém
    v
Asset (value object imutável; symbol)

Iterable[Transaction]
    | rebuild_positions (replay integral)
    v
ReconstructionResult (imutável)
    +-- positions: tuple[Position, ...]        (somente abertas)
    +-- closed_positions: tuple[Position, ...] (realizado preservado)
                   +-- portfolio_id + Asset
```

## Asset

Value object frozen/slots com symbol: str. Exige string, aplica strip().upper()
e rejeita símbolo vazio. Igualdade/hash usam o símbolo normalizado:
`Asset(" petr4 ") == Asset("PETR4")`. Aceita AAPL, BTC-USD e BRK.B sem restringir
ao formato B3. Não existem subclasses por categoria.

## Transaction e TransactionType

Enum contém exatamente BUY e SELL. Transaction possui id: int | None,
portfolio_id: int, asset: Asset, transaction_type: TransactionType,
quantity: Decimal, unit_price: Decimal, fees: Decimal e occurred_at: datetime.
ID opcional fica no fim do construtor, como Portfolio.

IDs informados devem ser inteiros positivos, excluindo booleanos. Quantidade e
preço são Decimal finitos estritamente positivos; taxas são Decimal finitas
não negativas. Não aceita conversão implícita de float, int ou str. Quantidades
fracionárias são válidas. Asset, Enum e datetime são validados em execução.

Entidade frozen/slots: como Portfolio, entidades com ID são iguais pelo ID;
sem ID, somente pela identidade do objeto. Reconstrução não elimina operações
pela igualdade: cada entrada é processada, inclusive empates completos.
Existência da carteira é garantida pela FK na Infrastructure; a entidade não
acessa o banco. Transaction.amounts encapsula bruto e custo/receita líquida com
Decimal local, compartilhando a política de taxas com reconstrução e exibição.

## Position e resultado

Snapshot imutável derivado, sem identidade própria, tabela, modelo ORM ou
repository. Campos: portfolio_id, asset, quantity, average_cost, cost_basis e
realized_profit_loss. Os quatro valores financeiros são Decimal. Resultado
realizado pode ser negativo. Quantidade/custo são não negativos; posição aberta
exige custo/média positivos; encerrada exige quantidade/custo/média zero exato.
Não contém cotação, valor atual, rentabilidade ou lucro não realizado.

ReconstructionResult.positions contém somente abertas. closed_positions retém
snapshots encerrados e seus resultados realizados. Ambas são tuplas ordenadas
por (portfolio_id, asset.symbol). Na recompra, a posição volta à coleção aberta
com resultado realizado acumulado preservado.

## Reconstrução e ordenação

`domain/reconstruction.py` oferece
`rebuild_positions(transactions: Iterable[Transaction]) -> ReconstructionResult`.
Materializa o iterável uma vez, valida, ordena e reconstrói estado local do zero
por (portfolio_id, Asset), sem modificar entradas. Histórico vazio produz duas
tuplas vazias. Venda sem saldo lança InsufficientPositionError, derivada de
DomainValidationError; nenhum resultado parcial é devolvido. Validação de
objetos usa DomainValidationError, compatível com ValueError.

Critério: occurred_at ASC, IDs conhecidos crescentes e desempate estável pela
ordem de entrada. No mesmo timestamp, entradas com ID precedem as sem ID;
entradas sem ID mantêm ordem relativa e empates completos também. Trocar a ordem
de entradas sem desempate identificável pode mudar o resultado. Não há
suposição de que toda compra anteceda vendas no mesmo timestamp.

Datas podem ser todas naive ou todas aware; mistura é rejeitada com erro de
domínio. Datas aware são ordenadas pelo instante UTC, sem timezone externo nem
alterar Transaction. Históricos fora de ordem são integralmente reprocessados,
permitindo retroatividade validada sem depender de Position persistida.

## Custo médio e taxas

Compra:

```text
purchase_cost = quantity * unit_price + fees
new_cost_basis = previous_cost_basis + purchase_cost
new_quantity = previous_quantity + quantity
average_cost = new_cost_basis / new_quantity
```

10 @ 30 + taxa 2 resulta em quantidade 10, custo 302 e média 30.2.
Outra compra de 10 @ 40 + taxa 2 resulta em quantidade 20, custo 704 e média 35.2.

Venda parcial:

```text
removed_cost = sell_quantity * previous_average_cost
net_proceeds = sell_quantity * unit_price - fees
realized_delta = net_proceeds - removed_cost
new_cost_basis = previous_cost_basis - removed_cost
new_quantity = previous_quantity - sell_quantity
average_cost = previous_average_cost
realized_profit_loss += realized_delta
```

Vender 5 @ 42 com taxa 1 produz receita líquida 209, custo removido 176,
resultado realizado 33, quantidade 15, custo 528 e média 35.2.
Taxas de venda reduzem receita, sem alterar a média remanescente.

Na venda total, custo removido é o custo restante exato, absorvendo resíduos da
divisão periódica do custo médio. Quantidade/custo/média recebem Decimal zero
exato. Resultado realizado permanece. Recompra inicia nova base sem média antiga:
BUY 10 @ 20, SELL 10 @ 30, BUY 5 @ 50 resulta em quantidade 5, custo 250,
média 50 e resultado realizado 100.

## Precisão Decimal

Sem float, conversão indireta ou quantize monetário. Context novo em localcontext,
ROUND_HALF_EVEN e mínimo 50 algarismos significativos. Entradas extensas ampliam
a precisão previsivelmente:

```text
span = max(value.adjusted()) - min(value.as_tuple().exponent) + 1
precision = max(50, 2 * span + digits(number_of_transactions_for_this_position) + 10)
```

Valores considerados: quantidade, preço e taxas do histórico de cada
(portfolio_id, Asset), sem influência de carteiras ou ativos independentes. Reserva
precisão para magnitude, escala, produtos e somas de entrada. Divisões periódicas
são finitas conforme esse contexto. Acrescentar entradas pode ampliar a precisão
de uma reconstrução integral. Contexto global, traps, arredondamento e flags
não mudam. Formatação monetária/arredondamento visual pertencem à apresentação.

## POO e limites

Asset demonstra value object; Portfolio/Transaction são entidades; Enum limita
tipos; frozen/slots e validação encapsulam invariantes. Transaction contém Asset
e referencia Portfolio por identidade. Position contém Asset. Reconstrução
abstrai replay sem service layer genérica, herança artificial ou dependências
de ORM, HTTP e PySide6. calculations permanece para indicadores, projeções,
risco e valuation. PriceAlert, edição/exclusão, dividendos,
splits, transferências e impostos continuam futuros. Ledger já é persistido.

Referências: [ADR-001](decisions/ADR-001-transaction-ledger.md),
[ARCHITECTURE.md](ARCHITECTURE.md) e [DATABASE.md](DATABASE.md).

## Integração no incremento 03

TransactionRepository é contrato append-only do domínio, implementado fora dele.
IDs novos são crescentes globalmente. order_transactions centraliza o critério
usado pelo replay e pelas listagens. InsufficientPositionError expõe carteira,
símbolo, saldo e quantidade solicitada para mensagens compreensíveis da UI.
A Application valida histórico + candidato antes da persistência; mesma data
mantém a interpretação financeira após atribuição do ID. Datas da UI são naive;
API do domínio continua aceitando históricos inteiramente aware.


## Mercado e valuation — Grande Incremento 04

Quote, HistoricalPrice, PriceHistory e AssetSearchResult são snapshots/value
objects imutáveis independentes do provider. Preços são Decimal; timestamps de
mercado são aware, separados das datas históricas naive aceitas pelo ledger.
MarketDataProvider é ABC de consulta em lote, cotação individual, busca e histórico;
QuoteBatch permite falhas por ativo sem descartar outras cotações.

Position mantém quantidade, média, custo e realizado derivados exclusivamente do
ledger. ValuedPosition compõe Position + Quote e métricas temporais, sem alterar
entidades ou schema. PortfolioValuation inclui realizado das encerradas. Ambos
vivem em calculations/valuation, junto à função pura value_portfolio.

Valor atual = quantidade × preço; não realizado = valor atual - custo restante;
retorno aberto = não realizado / custo restante quando >0; total = realizado +
não realizado. Mercado agregado exige todas as posições disponíveis em BRL;
moeda diferente mantém preço/valor na moeda própria e não é convertida. Ausência
é None, distinta de zero legítimo de carteira sem posições. Não há retorno total
percentual ou patrimônio incluindo caixa fictício.

Regras completas: [API_ARCHITECTURE.md](API_ARCHITECTURE.md).
