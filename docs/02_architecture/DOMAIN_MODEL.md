# Modelo de domínio do CORE MVP

## 1. Princípio do modelo

O histórico de transações é a fonte de verdade. Posições, preço médio, custo
total e alocação são derivados. Isso mantém o modelo auditável e evita
sincronizar duas representações persistidas do mesmo fato.

```text
Portfolio (transitório, sem ID e sem tabela)
  compõe 0..* Transaction
                 |
                 +-- possui 1 Asset
  deriva 0..* Position

Transaction é persistida.
Asset, Position e Portfolio não têm tabela no CORE.
```

## 2. Objetos principais

### `Asset`

Objeto de valor imutável, não uma entidade persistida no CORE.

- dado: `symbol` normalizado (sem espaços externos e em maiúsculas);
- regra: código não vazio e limitado a tamanho documentado;
- igualdade: pelo código normalizado;
- não possui subclasses `Stock`, `FII` ou `ETF`.

O CORE não tem comportamento diferente por classe de ativo. Uma hierarquia
seria apenas classificatória e, portanto, artificial. Se o MVP EXTENDED exigir
metadados, um tipo/enumerador ou tabela de ativos pode ser avaliado então.

### `Transaction`

Entidade imutável e persistida.

- identidade: `id` UUID gerado pela aplicação/domínio;
- `asset: Asset`;
- `type: TransactionType` (`BUY` ou `SELL`);
- `quantity: Decimal`;
- `unit_price: Decimal`;
- `occurred_at: datetime`;
- `created_at: datetime` para desempate/auditoria.

Invariantes:

- quantidade e preço unitário maiores que zero;
- ativo válido;
- datas válidas segundo regra definida antes da implementação;
- tipo limitado ao enum;
- valor bruto é `quantity * unit_price` e não é persistido.

Compra e venda não serão subclasses: os dados são os mesmos e a variação de
regra ocorre ao aplicar a transação ao portfólio. O enum é mais claro.

### `Position`

Objeto de valor imutável, calculado por ativo e nunca persistido no CORE.

- `asset`;
- `quantity`;
- `average_price`;
- `cost_basis` (`quantity * average_price`).

Persisti-la duplicaria dados e criaria risco de divergência após erro, exclusão
ou mudança de regra. Para o volume acadêmico, recalcular a partir do histórico é
simples. Materialização só deve ser considerada com evidência de desempenho.

### `Portfolio`

Objeto de domínio transitório, não entidade persistida.

Há apenas uma carteira no CORE e ela não precisa de nome, ID ou ciclo de vida
próprio. `Portfolio` existe porque concentra comportamento útil:

- ordenar e aplicar transações;
- validar venda contra posição disponível;
- derivar posições;
- calcular custo total;
- calcular alocação por custo.

Ele é construído a partir de `list[Transaction]` em cada caso de uso de leitura
ou validação. Se múltiplas carteiras entrarem no escopo futuro, identidade e
persistência serão reavaliadas.

## 3. Regra de posição e preço médio

As transações são processadas por `occurred_at`, depois `created_at` e `id` como
desempate determinístico.

Para compra:

```text
novo_custo = custo_atual + quantidade_compra * preco_compra
nova_quantidade = quantidade_atual + quantidade_compra
novo_preco_medio = novo_custo / nova_quantidade
```

Para venda:

- rejeitar se a quantidade vendida exceder a disponível;
- reduzir a quantidade;
- manter o preço médio da posição remanescente;
- reduzir o custo pelo preço médio anterior, não pelo preço da venda;
- remover a posição derivada quando a quantidade chegar a zero.

O preço de venda fica no histórico, mas lucro realizado e impostos estão fora
do CORE. Inserção retroativa só é aceita se a recomposição cronológica completa
continuar válida; caso contrário, toda a operação é rejeitada.

## 4. Precisão numérica

- usar `Decimal`, nunca `float`, para quantidade, preço e custo;
- quantidade: até 8 casas decimais;
- preço unitário: até 4 casas decimais no CORE;
- cálculos mantêm precisão decimal; arredondamento de exibição não altera o
  valor interno;
- definir `ROUND_HALF_UP` apenas nos pontos explícitos de apresentação ou
  persistência;
- porcentagens do gráfico podem ser arredondadas somente no DTO/UI.

Essas escalas são uma decisão inicial simples; devem ser cobertas por testes
antes de aceitar valores nos limites.

## 5. Validações do domínio

Erros específicos derivados de `DomainError`:

- `InvalidAssetError`;
- `InvalidQuantityError`;
- `InvalidPriceError`;
- `InvalidTransactionDateError`;
- `InsufficientPositionError`;
- `InvalidTransactionHistoryError`.

Os nomes podem ser ajustados durante a primeira vertical slice, mas não se deve
criar uma classe de erro para cada campo sem benefício. A UI não conhece como a
regra é calculada; apenas transforma o erro em mensagem amigável.

## 6. Entidades versus objetos derivados

| Objeto | Classificação | Persistido? | Justificativa |
|---|---|---:|---|
| `Transaction` | Entidade | Sim | Possui identidade e representa fato histórico auditável. |
| `Asset` | Objeto de valor | Não | No CORE, apenas o código identifica o conceito e está na transação. |
| `Position` | Objeto de valor/projeção | Não | É consequência determinística do histórico. |
| `Portfolio` | Objeto/agregador transitório | Não | Carteira única sem ciclo de vida ou identidade própria. |

## 7. Conceitos de POO no modelo

- encapsulamento nas invariantes de criação e aplicação das transações;
- associação entre `Transaction` e `Asset`;
- composição de transações dentro da visão `Portfolio`;
- abstração em objetos que representam apenas conceitos relevantes;
- polimorfismo fora do domínio, no contrato de repositório;
- herança deliberadamente ausente por falta de relação semântica necessária.
