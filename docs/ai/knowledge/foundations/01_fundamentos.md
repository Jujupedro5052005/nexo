# 01 — Fundamentos de valuation

Versão 2.0 · referência técnica Nexo · revisão 03/11/2026.

## Problema e objetos diferentes

Valuation estima quanto um conjunto de direitos econômicos pode valer sob
hipóteses explícitas. Preço é uma observação de mercado, em um horário e moeda;
valor é o resultado de um modelo, em uma data-base. Preço médio de compra é uma
informação do investidor. Nenhum dos três substitui os outros. Uma perda de 40%
desde a compra não demonstra desconto em relação ao valor; lucro acumulado não
demonstra que a tese se esgotou. O modelo precisa representar os direitos da
ação, cota, dívida ou participação efetivamente analisada.

Há três famílias úteis: fluxos descontados, comparação relativa e patrimônio
ajustado. Fluxos tornam as hipóteses de geração de caixa visíveis; múltiplos
comparam o preço de características econômicas; patrimônio ajustado investiga o
valor dos ativos líquidos. Essas abordagens podem discordar sem que exista um
erro aritmético. O analista deve explicar a hipótese responsável pela diferença,
em vez de tirar uma média sem significado econômico.

## Valor presente, moeda e direitos

Para um fluxo certo F recebido em n períodos, VP = F/(1+r)^n. Para uma sequência,
VP = Σ F_t/(1+r_t)^t, quando r_t representa a taxa equivalente até cada prazo.
A taxa é um custo de oportunidade compatível com risco, moeda, prazo e natureza
do fluxo. Fluxos destinados aos acionistas usam custo de capital próprio; fluxos
antes dos pagamentos aos financiadores usam taxa compatível com a firma.
Misturar dividendo com WACC ou lucro contábil com fluxo livre altera o objeto.

Valores nominais exigem taxas nominais; fluxos em poder de compra constante
exigem taxas reais. Unidade monetária também importa: R$ mil, R$ milhões e valor
por ação são grandezas diferentes. O sistema deve preservar unidade original,
fazer conversão explícita e dividir pelo número economicamente adequado de ações,
considerando diluição quando pertinente. Não há conversão cambial implícita.

## Caso sintético completo

Uma participação paga 12 BRL ao fim de cada um dos próximos dois anos e 112 no
terceiro, incluindo liquidação. Com r=10%, os termos são 10,9091, 9,9174 e
84,1473; VP≈104,9737. Se a cotação for 90, a diferença sobre preço é
104,9737/90−1≈16,64%. A margem observada sobre valor é
(104,9737−90)/104,9737≈14,26%. São percentuais com denominadores distintos.
Um desconto de segurança de 20% gera preço teto de aproximadamente 83,9790.
Assim, preço inferior ao valor teórico ainda pode superar o teto escolhido.

Se a taxa subir para 12%, mantendo os fluxos, VP cai para aproximadamente
100. A conclusão não é que o mercado necessariamente corrigirá o preço, mas que
uma exigência de retorno maior reduz o valor presente das mesmas promessas.
Uma alteração nos fluxos deve ser analisada separadamente da alteração na taxa.
Não se atribui probabilidade a esses cenários sem um modelo estatístico próprio.

## Segurança não é uma correção automática

O desconto de segurança é uma escolha analítica aplicada a um valor já
condicional. Não transforma dados ruins em bons dados nem torna todos os riscos
equivalentes a uma redução de 20%. Quanto maior a fragilidade da avaliação,
mais útil pode ser apresentar intervalo e condições de invalidação. Um passivo
contingente material pode exigir cenário específico, e não somente outro desconto.
Limites de posição dependem também da carteira e não emergem dessa fórmula.

## Limites e escolhas auditáveis

Valor terminal muito dominante, taxas próximas do crescimento, número de ações
desatualizado, lucros negativos e distribuição extraordinária são sinais para
revisão. Uma avaliação não deve esconder quanto veio de um terminal distante.
Também não é correto somar caixa duas vezes, descontar dívida em modelos de
equity que já a incorporam ou tratar valor da firma como valor por ação.
Quando direitos, moeda ou passivos não podem ser reconciliados, a avaliação fica
parcial. Informação ausente permanece ausente; não recebe zero por conveniência.

Na implementação Nexo, uma análise deve registrar identificação do ativo, data
de consulta e data efetiva de cada informação, método e versão, todas as entradas,
origem das hipóteses, fórmula e saídas. A precisão é mantida nos cálculos, e o
arredondamento ocorre na apresentação. O parecer pode ser favorável dentro de um
cenário e, simultaneamente, desaconselhar ampliar uma posição concentrada.

## Roteiro de revisão

Recalcule a soma dos fluxos com exemplos conhecidos; mude uma taxa mantendo os
fluxos; separe diferença sobre preço e margem sobre valor; teste moeda divergente,
ausência de cotação e eventos de diluição. Reavalie após resultados, mudanças
de capital ou quebra de premissas. A fonte de uma cotação atual não comprova a
qualidade dos fluxos projetados. O corpus é apoio à interpretação: a execução
financeira continua fora do copiloto.

## Referências

- [Damodaran — materiais de valuation, NYU Stern](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/valuation/val.htm): organização das abordagens.
- [CVM — acesso a informações de emissores](https://www.gov.br/cvm/pt-br/acesso-a-informacao-cvm/perguntas-frequentes-da-cvm/como-acessar-dados-informacoes-sobre-regulados): verificação documental.
- Cálculos, exemplos e critérios operacionais deste capítulo são elaboração
  original do Nexo, sem reprodução dos exemplos numéricos dessas fontes.
