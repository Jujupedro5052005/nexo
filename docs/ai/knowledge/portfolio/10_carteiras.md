# 10 — Análise de carteiras e gestão de risco

Versão 2.0 · referência técnica Nexo · revisão 03/11/2026.

## Estado atual e trajetória são objetos distintos

Peso atual de uma posição é seu valor de mercado dividido pelo valor aberto
compatível da carteira. Isso não equivale à proporção dos aportes históricos.
Retorno não realizado sobre custo aberto descreve uma fotografia; não é uma
medida de performance histórica que considere todos os fluxos. O Nexo preserva
essa distinção e não incorpora caixa desconhecido à fotografia de posições.

Se falta cotação de uma posição ou conversão de moeda necessária, pesos agregados
podem ficar indisponíveis. Renormalizar somente os ativos conhecidos faz a
concentração parecer diferente da real. O relatório precisa apresentar o
motivo da indisponibilidade e conservar os valores locais do ledger, em vez de
inventar uma avaliação completa.

## Concentração por ativo e fator

Maior peso, soma dos três maiores e HHI=Σw_i² são descrições reproduzíveis.
HHI de uma carteira com quatro posições iguais é 0,25; de duas posições de
50% é 0,50. Nenhum número isolado fornece um limite adequado a todo investidor.
Um limiar de 25% usado pela política ilustrativa do Nexo é uma configuração
analítica, não um fato universal nem autorização para vender uma posição.

Setores, moedas, grupos econômicos e fatores comuns exigem uma classificação
rastreável. Dois tickers diferentes podem compartilhar controlador ou exposição
a juros, commodity e regulação. "Não classificado" é uma categoria legítima.
O sistema não deduz um setor financeiro preciso somente pelo formato do ticker.
A classificação pequena e curada do Nexo declara sua cobertura limitada.

## Volatilidade, correlação e carteira

Retorno simples entre dois fechamentos é r_t=P_t/P_(t−1)−1, sob uma base de
ajuste compatível. A volatilidade amostral usa desvio padrão com denominador
n−1 para n retornos. Annualização por √252 é uma convenção que pressupõe
frequência diária e limitações de dependência temporal. Não se aplica diretamente
a observações mensais ou a uma sequência irregular chamada de diária.

Para dois ativos, variância da carteira é w_A²σ_A²+w_B²σ_B²+
2w_Aw_Bρσ_Aσ_B. Exemplo sintético: pesos 50%/50%, volatilidades 20%/30% e
correlação zero produzem σ≈18,03%. Com correlação 1, σ=25%; com −1, σ=5%.
O resultado mostra uma relação matemática, sem demonstrar que correlações
históricas sobreviverão a uma crise. Correlação exige retornos nas mesmas datas;
alinhar pelo índice de linha pode comparar dias diferentes silenciosamente.

## Drawdown e cauda

Drawdown em t é P_t/max(P_0…P_t)−1. Numa série 100,120,90,110, o pior valor
é −25%, medido do pico 120 para 90; não −10% em relação ao ponto inicial.
Uma recuperação até 110 ainda não eliminou a queda desde o pico. O máximo
drawdown observado não é limite de perda futura.

Volatilidade mede dispersão, não todos os riscos. Dados esparsos, iliquidez,
eventos descontínuos, correlações em estresse e passivos fora do preço podem
escapar à amostra. Não se transforma um número de volatilidade em probabilidade
de falência. Um gráfico de patrimônio também exige caixa e fluxos coerentes;
um gráfico de cotações de ativos não deve receber o título de evolução patrimonial.

## Aportes e rebalanceamento hipotético

Com valor total 1.000 e posição A de 300, aporte externo de 200 em outro ativo
reduziria o peso de A para 25%, se preços fossem constantes e não houvesse custos.
Um aporte de 200 em A elevaria seu peso para 500/1.200≈41,67%. Essa análise
ajuda a discutir alternativas de alocação sem enviar qualquer ordem. Deve-se
explicitar que o denominador mudou e que os preços podem mudar antes da execução.

Um parecer de rebalanceamento combina concentração, qualidade, valuation e
objetivos que tenham sido informados. Ausência de perfil pessoal não é licença
para inventá-lo. O relatório pode priorizar investigação e apresentar hipóteses
de exposição, reservando decisões pessoais essenciais ao usuário.

## Implementação e revisão

Use transações e eventos como fonte da reconstrução, sem persistir outra posição
concorrente. Conserve datas, ajustes, moeda e origem das séries. Teste pesos
conhecidos, ausência de uma cotação, série constante, datas desencontradas e
cancelamento no meio da investigação. Avaliações agregadas precisam corresponder
às mesmas bases individuais. Uma nova movimentação invalida hipóteses de pesos
mesmo quando os fundamentos em cache continuam válidos.

## Referências

- [CVM — informações públicas e participantes](https://www.gov.br/cvm/pt-br/acesso-a-informacao-cvm/perguntas-frequentes-da-cvm/como-acessar-dados-informacoes-sobre-regulados): ponto de partida para rastreabilidade.
- [Nexo — arquitetura financeira e políticas implementadas](../../../02_architecture/FINANCIAL_TOOLS.md): limitações de patrimônio e retorno no aplicativo.
- Fórmulas e exemplos são derivações matemáticas sintéticas apresentadas para
  validação do software; não reproduzem resultados de um estudo empírico.
