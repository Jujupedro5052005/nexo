# ADR-001 — Transações como fonte principal de verdade financeira

- **Status:** aceito
- **Data:** 2026-08-25

## Contexto

Persistir simultaneamente transações e posições calculadas duplicaria o estado
financeiro e poderia gerar divergências. `Portfolio`, contudo, possui identidade
e dados estruturais: uma carteira existe mesmo vazia e deve poder ser
selecionada e comparada a outras.

## Decisão

Persistir a identidade e os dados estruturais de `Portfolio` (ao menos `id` e
`name`), cada `Transaction` vinculada à carteira e, quando implementados,
`PriceAlert` e configurações necessárias.

Usar a coleção ordenada de `Transaction` como fonte principal de verdade
financeira. Reconstruir `Position`, quantidade consolidada, preço médio, valor
investido, lucro/prejuízo e rentabilidade quando necessários. `Asset` é tratado
principalmente como objeto de valor identificado pelo símbolo.

## Consequências positivas

- menor duplicação de estado;
- histórico auditável;
- consistência entre histórico e posições;
- facilidade para recalcular;
- melhor rastreabilidade por carteira.

## Consequências negativas

- reconstrução nas leituras e validações;
- maior custo de cálculo em algumas operações;
- lógica de agregação precisa ser correta e bem testada;
- alterações retroativas podem exigir revalidar o histórico.

## Exceção importante

`Portfolio` não é totalmente transitório. Sua identidade e seus dados
estruturais são persistidos porque o sistema suporta múltiplas carteiras. Apenas
o estado financeiro consolidado é reconstruído.

## Alternativas rejeitadas

- persistir `positions` como fonte paralela;
- manter uma única carteira global;
- criar `PositionRepository` para um estado derivado.

Projeções materializadas ou cache só devem ser avaliados mediante problema real
de desempenho; o ledger continua sendo a referência auditável.
