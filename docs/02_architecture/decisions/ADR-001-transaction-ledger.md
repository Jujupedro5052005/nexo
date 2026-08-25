# ADR-001 — Transações como fonte de verdade

- **Status:** aceito
- **Data:** 2026-08-25

## Contexto

O CORE precisa persistir compras e vendas, mostrar histórico, posições, preço
médio, custo e alocação. Persistir simultaneamente transações e posições
duplicaria o estado e exigiria sincronização em toda alteração ou falha.

Há apenas uma carteira local e o volume acadêmico esperado permite recalcular
as posições rapidamente.

## Decisão

Persistir somente transações. `Position` será uma projeção calculada do
histórico ordenado. `Portfolio` será um objeto transitório sem tabela ou ID, e
`Asset` será um objeto de valor representado pelo símbolo armazenado na
transação.

## Consequências positivas

- histórico auditável;
- uma única fonte de verdade;
- menor risco de divergência;
- schema e operações de escrita simples;
- regra de preço médio facilmente testável fora do banco.

## Consequências negativas

- leituras recalculam as posições;
- inserções retroativas exigem revalidar o histórico;
- volumes muito grandes podem exigir projeção/cache no futuro.

## Alternativas rejeitadas

- persistir `positions`: melhora leitura, mas duplica estado cedo demais;
- persistir `Portfolio`: não há múltiplas carteiras nem identidade necessária;
- tabela `assets`: o CORE não possui metadados ou ciclo de vida independente do
  ativo.

## Critério de revisão

Reavaliar somente se múltiplas carteiras, metadados próprios de ativos ou
medição de desempenho demonstrarem que o recálculo não atende ao produto.
