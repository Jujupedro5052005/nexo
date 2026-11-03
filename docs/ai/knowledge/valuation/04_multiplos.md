# 04 — Valuation por múltiplos

Versão 2.0 · referência técnica Nexo · revisão 03/11/2026.

## O que uma comparação realmente compara

Um múltiplo é uma razão entre uma medida de valor e uma medida econômica. P/L
relaciona preço ao lucro por ação; P/VP relaciona preço ao patrimônio por ação.
EV/EBITDA e EV/EBIT relacionam valor da firma a resultados antes de pagamentos
aos financiadores. Esses objetos não são intercambiáveis. Usar lucro líquido
como denominador de EV, por exemplo, mistura o efeito da dívida no numerador
com um resultado que já foi afetado pelo financiamento.

Múltiplos economizam explicitação de hipóteses, mas não as eliminam. Um P/L
menor pode refletir menor crescimento, risco maior, ciclo favorável no lucro
passado ou problema de governança. Selecionar uma mediana não demonstra que
as firmas compartilham risco, reinvestimento, margem e contabilidade comparáveis.
A amostra e suas exclusões precisam ser documentadas antes de conhecer a resposta.

## Equações e reconciliação

Para uma comparação por ação, preço de referência = LPA normalizado × P/L alvo,
ou VPA compatível × P/VP alvo. Para um múltiplo de firma, EV estimado = EBITDA
normalizado × EV/EBITDA alvo. Depois reconcilia-se equity: EV menos dívida
financeira líquida e outros direitos prioritários, com ajustes por participações
e ativos não operacionais que não estavam incluídos no fluxo. Somente então
divide-se pelo número diluído de ações correspondente.

Essa ponte exige definição consistente de dívida, caixa disponível, arrendamentos
e minoritários. Não é correto descontar a mesma dívida duas vezes. Um caixa
restrito não necessariamente reduz obrigações da mesma forma que caixa livre.
O Nexo executa inicialmente P/L e P/VP; a reconciliação por EV aqui explicada
é referência metodológica, sem prometer uma ferramenta de EV que não foi implementada.

## Caso sintético e hipóteses escondidas

Empresa A possui LPA recorrente de 4 BRL. Três pares comparáveis apresentam
P/L de 8, 10 e 14 vezes; a mediana é 10. Preço de referência=40. Com desconto
de 20%, teto=32. Se 1 BRL do LPA de A decorreu de venda não recorrente, o LPA
normalizado cai a 3: referência=30 e teto=24. Comprar a 28 parece descontado
no primeiro cálculo e acima do teto no segundo, sem qualquer mudança da cotação.

Em um exemplo distinto, EBITDA=100 milhões e múltiplo=6 geram EV=600 milhões.
Se dívida líquida=200 milhões, outros ajustes=0 e ações diluídas=20 milhões,
equity=400 milhões e valor por ação=20. Ignorar a dívida resultaria em 30 por
ação. Esse erro de reconciliação supera muitos refinamentos de seleção de pares.

## Seleção de pares e normalização

Compare produtos, geografia, moeda, fase de maturação, alavancagem e mix de
negócios. Compare também períodos: TTM, ano encerrado e projeção de consenso
não são o mesmo denominador. Um valor projetado deve vir com autoria, data e
dispersão, sem aparecer como resultado já publicado. O modelo não cria consenso
de analistas quando o provider não o oferece.

Normalizar significa demonstrar ajustes, não retirar todas as despesas que
desagradam. Reestruturações repetidas podem ser recorrentes economicamente.
Concilie lucro reportado ao ajustado, preserve perdas e registre hipóteses de
tributação sem presumir benefício fiscal garantido. Em negócios cíclicos, lucro
de pico comprime P/L e pode sinalizar maior risco de extrapolação, não barganha.

## Múltiplos por contexto

Bancos demandam análise de ROE, capital e crédito; EBITDA e dívida líquida
industriais podem não representar sua economia. FIIs exigem renda, patrimônio
e propriedades/recebíveis; lucro contábil não equivale a FFO, e LPA de uma
empresa não pode ser renomeado automaticamente como resultado de um fundo.
Para empresas que ainda não lucram, P/L negativo não é evidência de barateza.
Múltiplos de receita precisam de uma hipótese futura de margem e reinvestimento.

## Sensibilidade, limites e execução

Para LPA=4, múltiplos 8/10/12 produzem referências 32/40/48 e tetos descontados
25,60/32/38,40. Se simultaneamente se altera o lucro, a tabela deve indicar
ambas as variáveis. Uma comparação não pode misturar moeda do preço com moeda
do lucro. LPA/VPA ausentes ou não positivos impedem os métodos positivos
disponíveis; não recebem zero para completar a tabela.

O contrato registra métrica, múltiplo, justificativa de comparabilidade, fonte,
período e versão. A categoria "múltiplos" não autoriza executar uma expressão
gerada pelo Gemini. Testes usam resultados conhecidos e rejeitam métricas
incompatíveis. O parecer deve dizer qual ajuste ou diferença entre pares faria
a comparação perder validade, em vez de tratar a mediana como valor intrínseco exato.

## Referências

- [Damodaran — Research and Papers, Valuation Multiples](https://people.stern.nyu.edu/adamodar/New_Home_Page/papers.html): referência para princípios de comparação relativa.
- [CVM — informações periódicas de companhias](https://sistemas.cvm.gov.br/port/ciasabertas/menu4.asp): fonte para reconciliações documentais.
- Exemplos e especificação operacional originais Nexo; não contêm estimativas atuais de empresas reais.
