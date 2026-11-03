# 06 — Seguradoras e holdings financeiras

Versão 2.0 · referência técnica Nexo · revisão 03/11/2026.

## Subscrição e resultado financeiro

Seguradoras recebem prêmios em troca de obrigações contingentes. O prêmio não
é todo lucro nem caixa livre para distribuir. Há despesas comerciais, sinistros,
resseguro, despesas administrativas e necessidades de reservas/capital. Uma
análise deve decompor o resultado de subscrição do resultado financeiro, evitando
atribuir a uma melhora operacional um ganho transitório com aplicações.

Sinistralidade relaciona sinistros a uma base de prêmios compatível; o índice
combinado acrescenta despesas segundo a definição utilizada. Bases emitidas,
ganhas, retidas e líquidas de resseguro podem diferir. Antes de comparar empresas,
registre definição, período e ramo. A disponibilidade de indicadores em painéis
da SUSEP não significa que o aplicativo já os possua; quando faltam, o parecer
deve declarar que a qualidade da subscrição ainda não foi verificada.

## Caso sintético de subscrição

Considere prêmios ganhos de 100, sinistros de 60 e despesas de 30, em milhões.
Índice combinado simplificado=(60+30)/100=90%, com resultado de subscrição=10.
Se aplicações geram 12, o resultado antes dos demais ajustes é 22. Em cenário de
sinistros=75 e financeiro=5, a subscrição passa a −5 e o agregado a zero.
O yield de dividendos passado não revelaria sozinho esse risco de mudança.

Esse exemplo exclui impostos, variação de reservas e outras contas para tornar
a ponte numérica auditável. Não se chama essa conta simplificada de lucro líquido
regulatório. Se uma empresa divulgar índice combinado em escopo diferente, o
software não deve tentar reproduzi-lo sem sua reconciliação. Provisões liberadas
podem elevar lucro num período sem representar melhora recorrente de precificação.

## Reservas e qualidade da distribuição

Examine adequação de provisões, desenvolvimento de sinistros antigos,
resseguradores, concentração de riscos, liquidez e capital. Sinistros de cauda
longa envolvem incerteza de valor e prazo. Inflação de custos pode afetar
obrigações mesmo quando a receita foi recebida antes. Duration de ativos e
passivos ajuda a interpretar juros, mas uma alta de taxa não melhora todos os
resultados simultaneamente: pode reduzir valor de ativos e alterar obrigações.

Distribuição depende da capacidade de liberar capital, não apenas do lucro
consolidado. Um parecer que usa o último dividendo como renda perpetuamente
sustentável precisa demonstrar por que reservas e capital continuarão adequados.
Sem esses dados, o Nexo pode oferecer um cenário identificado de repetição,
sem elevar a confiança por causa da precisão dos centavos.

## Holdings: soma das partes e dupla contagem

Uma holding pode receber dividendos de controladas, ter despesas próprias,
caixa, dívida e restrições de transferência. Não é automaticamente um banco
porque participa de um banco. A soma das partes estima a participação econômica
em cada negócio e reconcilia com obrigações e ativos da holding. O desconto
observado não prova que todo o hiato será eliminado.

Exemplo sintético: participação A vale 600, participação B vale 200, caixa da
holding=50, dívida=150 e valor presente de despesas próprias=40. Valor líquido
estimado=660. Se mercado=600, desconto sobre valor≈9,09%. Aplicar outro desconto
de 20% a 660 leva a teto=528. Uma cotação abaixo da soma das partes ainda pode
estar acima desse teto. Não se soma novamente o caixa de uma controlada já
avaliada por equity com esse caixa incorporado.

## Métodos e revisão

DDM e retorno excedente podem organizar hipóteses para instituições financeiras;
soma das partes pode ser mais apropriada a holdings. Múltiplos exigem pares
com ramo e capital comparáveis. O código atual não estima reservas atuariais
nem soma das partes automaticamente. O catálogo deve distinguir método descrito
de método executável. Não é permitido inferir probabilidade de insolvência com
base em índice combinado isolado.

Registre evolução de prêmios, sinistros, capital, definição de indicadores,
fonte e período. Confirme se um provento é recorrente ou extraordinário, bruto
ou líquido. Reavalie o parecer após mudanças de precificação, resseguro, reservas
e estrutura da holding. Posição excessiva na carteira pode justificar conter
novos aportes mesmo sob cenário favorável do negócio; isso é uma conclusão
condicional de exposição, não uma ordem de execução.

## Referências

- [SUSEP — Central de Painéis](https://www.gov.br/susep/pt-br/central-de-conteudos/central-de-paineis): indicadores de mercado e escopos a verificar.
- [SUSEP — relatórios de acompanhamento](https://www.gov.br/susep/pt-br/central-de-conteudos/dados-estatisticos/relatorios-de-analise-e-acompanhamento-dos-mercados-supervisionados-1): investigação setorial.
- Exemplos, reconciliação e roteiro de implementação são originais Nexo; não reproduzem um balanço real.
