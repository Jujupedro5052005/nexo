# 02 — Dividend Discount Model e Gordon

Versão 2.0 · referência técnica Nexo · revisão 03/11/2026.

## Objeto e hipótese econômica

O modelo desconta distribuições futuras aos titulares da ação. Não afirma que
todo lucro será distribuído nem que dividendos passados representam automaticamente
o próximo pagamento. D1 é o dividendo esperado do próximo período; D0 é o
dividendo da data-base. Se o crescimento de D0 para D1 é assumido, deve-se
registrar D1=D0(1+g), evitando aplicar crescimento duas vezes.

Com pagamentos anuais e crescimento constante, D_t=D1(1+g)^(t−1). O valor é
Σ[D1(1+g)^(t−1)/(1+Ke)^t]. Colocando D1/(1+Ke) em evidência, resta uma série
geométrica de razão q=(1+g)/(1+Ke). Sua soma converge para 1/(1−q) se |q|<1.
No domínio econômico usual, com g>−1 e Ke positivo, isso exige Ke>g. Portanto,
P0=D1/(Ke−g). Não é permitido ignorar a restrição porque o software conseguiu
efetuar a divisão: denominador zero ou negativo destrói a interpretação estável.

## Crescimento financiável

Sob ROE constante, ausência de emissão e patrimônio que cresce por lucros retidos,
g≈ROE×retenção. Essa relação exige consistência de período e clean surplus;
não prova que o ROE passado sobreviverá. Um payout de 100% acompanhado de alto
crescimento perpétuo precisa de explicação sobre financiamento. Crescimento que
demanda reinvestimento tende a reduzir a distribuição disponível hoje. Tratar g
como variável gratuita superestima valor sem pagar pelo investimento necessário.

Ke representa retorno requerido para o risco do equity. Um número sugerido por
IA é uma hipótese estimada, com justificativa, não observação. Beta, prêmio de
risco, taxa livre de risco e ajuste de país podem ajudar sua construção, mas
precisam de fontes, moeda e data. O Nexo não infere Selic atual a partir do
conhecimento do modelo nem chama uma faixa ilustrativa de taxa de mercado.

## Exemplo sintético e sensibilidade

Assuma D1=3 BRL, Ke=10% e g=4%. P0=3/0,06=50 BRL; com desconto de segurança
de 20%, teto=40. Cotação 35 implica diferença sobre preço de 42,8571% e margem
sobre valor de 30%. Esses números não são a expectativa de retorno em um prazo.

Mantendo D1 e g: Ke=9% produz valor 60; Ke=10%, 50; Ke=11%, aproximadamente
42,8571. Mantendo D1 e Ke: g=3% produz 42,8571; g=4%, 50; g=5%, 60. A derivada
∂P/∂Ke=−D1/(Ke−g)² e ∂P/∂g=D1/(Ke−g)² demonstra por que a sensibilidade
explode perto do limite. Essa é uma propriedade do modelo, não uma certeza
econômica sobre empresas com pequeno spread entre as duas taxas.

Um cenário conservador pode combinar menor dividendo sustentável e maior Ke,
enquanto outro explora recuperação. Ao mudar várias entradas, apresente todas;
uma análise de uma variável por vez não deve ser chamada de previsão de cenário
macroeconômico completo. A ordenação conservador/base/otimista deve corresponder
às saídas, não apenas à ordem em que um modelo enviou os parâmetros.

## Aplicabilidade e alternativas

O modelo estável é mais interpretável quando a distribuição e a estrutura de
capital possuem alguma estabilidade. Crescimento extraordinário, reorganizações,
restrições regulatórias ou payout muito distante da capacidade de distribuir
pedem múltiplos estágios ou outra representação dos fluxos. Não pagar dividendos
agora não implica que a firma vale zero; pode tornar Gordon inadequado para
aquele caso. Também não se deve financiar crescimento perpétuo acima de toda a
economia indefinidamente sem discutir sua plausibilidade.

O modelo de dois estágios calcula dividendos explícitos nos anos 1 a N e um
terminal D_(N+1)/(Ke_estável−g_estável), descontando o terminal até hoje. O
dividendo terminal precisa refletir o payout do estado estável. Esse desenho
está descrito para referência; não é automaticamente executado pelo método
Gordon de um estágio disponível no formulário.

## Contrato de implementação e revisão

Entradas monetárias usam Decimal e taxas em fração no motor; o formulário
aceita percentuais. D1 pode ser zero explícito, mas ausência não é zero. O
resultado deve informar hipótese de sustentabilidade, origem de D1, moeda,
fórmula e desconto. Taxas de até 12 casas e limites de magnitude evitam precisão
arbitrária. Cálculos de 3/(0,10−0,04), Ke=g, g negativo e dados ausentes integram
os testes. A cotação operacional só entra na comparação se pertencer ao mesmo ativo.

O parecer deve ser revisto quando distribuição, reinvestimento, risco do negócio
ou taxa requerida mudarem. Um texto antigo sobre Gordon pode fundamentar a
fórmula, mas não substituir o D1 estimado hoje. Esse vínculo entre documento,
premissa e dado operacional é parte da memória de cálculo auditável.

## Referências

- [Damodaran — Dividend Discount Model, NYU Stern](https://people.stern.nyu.edu/adamodar/pdfiles/eqnotes/ddm.pdf): referência conceitual; dados históricos da aula não são parâmetros atuais.
- [D'Amico e De Blasis — revisão de DDM (2020)](https://arxiv.org/abs/2001.00465): panorama dos modelos determinísticos e estocásticos.
- A derivação, as sensibilidades e os casos sintéticos acima são apresentados
  originalmente para a especificação do Nexo; não reproduzem exemplos das fontes.
