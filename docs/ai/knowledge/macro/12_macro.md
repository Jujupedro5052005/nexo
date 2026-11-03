# 12 — Cenário macroeconômico e investimentos

Versão 2.0 · referência técnica Nexo · revisão 03/11/2026.

## Transmitir mecanismos, não prever com falsa precisão

Juros, inflação, câmbio e atividade podem influenciar fluxos e taxas requeridas.
O efeito não é uniforme: depende da estrutura de receitas, custos, indexadores,
capital e dívida de cada negócio. Uma análise útil descreve o mecanismo e suas
premissas. Não basta escrever que "juros altos prejudicam ações" sem examinar
como mudam o fluxo e a taxa da companhia analisada.

O Banco Central publica histórico de taxas e informações de política monetária;
o IBGE publica o IPCA e sua metodologia. Esses indicadores têm definições,
datas de referência e divulgação. Meta Selic, taxa efetiva, taxa futura e retorno
de um investimento são grandezas distintas. O IPCA de um mês não equivale à
inflação acumulada em doze meses, e nenhum deles é automaticamente a inflação
futura incorporada a um fluxo de valuation.

## Consistência nominal e real

A relação exata simplificada é (1+r_nominal)=(1+r_real)(1+π). Assim,
r_real=(1+r_nominal)/(1+π)−1. Com números sintéticos r_nominal=12% e π=5%,
r_real≈6,6667%, e não exatamente 7%. A subtração é uma aproximação útil apenas
quando sua precisão é suficiente. Para descontar fluxos reais, a inflação usada
na conversão precisa ser coerente com as projeções, não simplesmente o último
número mensal disponível.

Em dois períodos com inflação de 4% e 6%, o acumulado é 1,04×1,06−1=10,24%,
não 10%. A mesma atenção vale à composição de retornos. Misturar taxa anual
com fluxo mensal sem conversão equivalente produz um erro dimensional. O motor
deve registrar frequência e horizonte, ainda que o formulário apresente taxas
anuais para facilitar a leitura.

## Curva, duration e custo de capital

Prazos diferentes podem ter taxas diferentes. Aplicar a taxa curta atual a
fluxos de dez anos pressupõe uma estrutura que precisa ser justificada.
Duration resume a sensibilidade de um conjunto de fluxos a uma mudança pequena
na taxa sob hipóteses de precificação. A aproximação ΔP/P≈−D_mod×Δy não
inclui todos os efeitos de convexidade, crédito ou mudanças não paralelas.

Num exemplo sintético com duration modificada 5 e aumento de 2 pontos percentuais,
a aproximação é −10%. Isso não atribui a toda ação uma queda de 10% numa alta
da Selic: fluxos e prêmios podem mudar ao mesmo tempo. A aplicação a uma empresa
exige seus próprios fluxos e não uma analogia automática com um título prefixado.

## Câmbio, atividade e exposições comuns

Uma exportadora pode receber moeda forte, importar insumos e manter dívida
externa. Uma empresa doméstica pode repassar inflação com atraso, perdendo margem
temporariamente. Um banco pode alterar margem financeira e custo de crédito em
direções diferentes. Uma carteira aparentemente distribuída entre setores pode
concentrar risco de juros ou crédito. A análise deve relacionar fatores a
posições e explicar onde não há dados suficientes para quantificar o efeito.

Não se inventa beta cambial, probabilidade de recessão ou cenário recente de
commodity porque o modelo reconhece o nome de uma companhia. Correlação
histórica não é demonstração causal; um anúncio macro e uma variação de preço
no mesmo dia também não bastam para atribuir causalidade.

## Cenários e protocolo de dados

Um cenário pode assumir taxa requerida de 12%, 14% ou 16%, com justificação
como faixa ilustrativa. Essas hipóteses não são a Selic atual, o custo de equity
estimado por um provider ou um consenso. No Nexo, o relatório informa quando
taxas, inflação e notícias atuais não foram consultadas. A biblioteca oferece
mecanismos conceituais, sem tentar funcionar como uma fonte de indicadores vivos.

Registre fonte oficial, série, unidade, frequência, competência, divulgação e
consulta. Expectativas de participantes são expectativas, não realizações.
Revisões de dados devem ter versão. Uma taxa historicamente correta pode estar
desatualizada para uma decisão presente. Sem dado atual, apresente simulação
condicional e a condição de revisão, preservando a distinção entre cálculo
exato e hipótese incerta.

## Referências

- [Banco Central — histórico das taxas básicas](https://bcb.gov.br/controleinflacao/historicotaxasjuros): definição e histórico a consultar, sem taxa atual incorporada ao texto.
- [IBGE — IPCA](https://www.ibge.gov.br/estatisticas/economicas/precos-e-custos/9256-ipca.html): definição, metodologia e divulgação.
- Fórmulas de equivalência, exemplos de composição e protocolo de cenários são
  elaboração original Nexo; nenhum valor do capítulo é previsão econômica.
