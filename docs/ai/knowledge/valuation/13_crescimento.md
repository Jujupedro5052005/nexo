# 13 — Avaliação de empresas de crescimento

Versão 2.0 · referência técnica Nexo · revisão 03/11/2026.

## Crescer exige recursos

Crescimento de receita não é equivalente a criação de valor. É necessário
conectar vendas, margens, investimento, capital de giro e risco. Uma empresa
pode crescer rapidamente e consumir caixa por muitos anos; pode também aumentar
lucro contábil sem gerar retorno sobre o capital incremental compatível com
seu custo. Uma narrativa de expansão precisa ser convertida em uma ponte
numérica verificável antes de fundamentar um preço teto.

Sob uma representação estável, crescimento operacional pode ser expresso como
taxa de reinvestimento × retorno sobre o capital investido. Essa relação é
uma aproximação de consistência, não uma licença para extrapolar ROIC histórico.
Aquisições, base contábil, intangíveis e diferenças entre retorno médio e
incremental podem alterar sua interpretação.

## DFC explícito e estado maduro

Um fluxo livre para a firma simplificado parte de resultado operacional após
tributos, soma despesas não desembolsáveis e subtrai investimento e capital
de giro operacional. Seu desconto exige taxa compatível com esse fluxo.
Uma avaliação de equity usa fluxo aos acionistas e custo próprio. Não se
misturam as duas estruturas apenas para chegar a um número desejado.

É possível projetar alguns anos de transição e depois um estado estável. O
terminal não deve perpetuar simultaneamente crescimento extraordinário,
reinvestimento baixo e margens que nunca foram demonstradas. O negócio maduro
precisa de uma hipótese de crescimento, retorno, reinvestimento e risco que
fechem entre si. Participação de mercado não pode crescer ilimitadamente numa
economia finita sem uma discussão sobre mudança de escopo.

## Caso sintético de reinvestimento

Considere lucro operacional após tributos de 100. Com crescimento sustentável
de 6% e ROIC de 12%, taxa de reinvestimento coerente é 50%; fluxo livre do
exemplo=50. Com o mesmo crescimento e ROIC de 20%, reinvestimento requerido
cai a 30%; fluxo livre sobe a 70. Empresas com crescimento igual podem gerar
valores diferentes pela eficiência do capital, não somente pela taxa de desconto.

Agora assuma que o custo de capital é 14%. Crescimento financiado a ROIC de
12% exige cautela: expandir esse padrão não demonstra criação de valor. Não
se conclui que a firma inteira tenha valor negativo; pode haver ativos existentes
rentáveis e opções estratégicas. O exemplo isola a economia do novo investimento.

## Diluição e qualidade da trajetória

Remuneração em ações, emissões e instrumentos conversíveis afetam o valor por
ação. Crescimento do lucro agregado pode coexistir com crescimento menor do
lucro por ação. Uma avaliação que ignora diluição pode atribuir aos atuais
acionistas direitos que serão divididos com outros investidores. Número de
ações e estrutura dos instrumentos precisam corresponder à data-base.

Receita contratada, usuários, volume ou outra métrica operacional precisam de
ponte para receita reconhecida, margem e caixa. Uma métrica de vaidade não
substitui valor econômico. A análise também deve distinguir rentabilidade
consolidada de rentabilidade de uma unidade mais madura usada como exemplo.

## Sensibilidade e casos inadequados

Num terminal sintético com fluxo do próximo ano de 10, taxa de 12% e crescimento
de 3%, valor terminal=111,1111. Se a taxa for 14%, cai a 90,9091; se crescimento
for 4% mantendo 12%, sobe a 125. Antes de interpretar a sensibilidade, confirme
que o fluxo de 10 já incorpora reinvestimento compatível com cada crescimento.
Caso contrário, a tabela muda g sem financiar seu efeito econômico.

P/L pode ser inaplicável a lucros negativos e EV/receita pode ocultar enorme
incerteza sobre margens futuras. Comparação relativa pode complementar um DFC,
mas não eliminar a necessidade de modelar a transição. Faltando dados para
simular uma transição razoável, o parecer permanece parcial.

## Implementação e revisão

O Nexo descreve esses métodos como referência; não executa automaticamente
um DFC detalhado sem especificação e entradas suficientes. Um agente não
pode gerar Python ou expressões livres para preencher essa lacuna. Métodos
operacionais novos precisam de contrato tipado, limites e exemplos independentes.

Registre hipóteses por período, origem, moeda, unidades, reinvestimento, margem,
ações e terminal. Mostre quanto do valor decorre de anos explícitos e do estado
maduro. Reavalie após divulgação de resultados, captação, mudanças competitivas
ou deterioração de retorno incremental. Uma conclusão direcional deve indicar
as condições que mudariam o parecer, sem prometer prazo de convergência da cotação.

## Referências

- [Damodaran — materiais de Investment Valuation](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/Inv2ed.htm): referência para aprofundamento dos modelos.
- [CVM — documentos financeiros e societários](https://sistemas.cvm.gov.br/port/ciasabertas/menu4.asp): verificação de estrutura e resultados.
- Exemplos e análise de consistência são originais Nexo e não descrevem uma
  empresa real nem um consenso de mercado.
