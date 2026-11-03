# 07 — Empresas de energia e utilities

Versão 2.0 · referência técnica Nexo · revisão 03/11/2026.

## Separar negócios antes de comparar

Geração, transmissão e distribuição possuem exposições distintas. Geração
envolve recurso energético, produção, contratos e eventuais diferenças entre
energia contratada e entregue. Transmissão exige leitura de concessões e receitas
relacionadas à disponibilidade. Distribuição incorpora demanda, perdas, qualidade
e processos tarifários. Agregar tudo como "elétricas de dividendos" esconde os
mecanismos que ligam o evento econômico ao caixa.

A ANEEL publica decisões e informações sobre receitas e tarifas. Uma receita
anual permitida deve ser lida com ciclo de vigência, componentes e ajustes,
sem converter automaticamente seu reajuste em crescimento do lucro ou do
dividendo. O capítulo não usa o reajuste de um ciclo passado como taxa atual.
Na análise aplicada, a data de publicação e o prazo contratual importam tanto
quanto o valor nominal.

## Fluxo, reinvestimento e concessão

Negócios com receitas relativamente previsíveis ainda precisam de manutenção,
investimentos, financiamento e capital de giro. EBITDA não incorpora CAPEX,
juros nem todos os efeitos tributários. Distribuir grande parte do lucro pode
ser possível numa fase de maturidade e inadequado no início de um ciclo de
expansão. O modelo precisa refletir esse calendário, em vez de projetar uma
política de payout constante por conveniência.

Concessões têm prazo e condições. Um terminal perpétuo sem discutir renovação,
indenização e investimento necessário pode avaliar um direito que a companhia
não possui. A alternativa é explicitar fluxos até o fim do contrato e tratar
renovação como cenário separado. Não se presume recebimento integral de uma
indenização controvertida nem seu prazo de pagamento.

## Exemplo sintético de caixa

Receita anual=100, custos desembolsáveis=30, investimento de manutenção=20,
juros=15 e tributos pagos=10. Uma ponte simplificada deixa 25 antes de outras
necessidades de caixa. Lucro contábil de 40, se existente, não autoriza afirmar
que os 40 são distribuíveis. Se CAPEX temporariamente sobe a 40, o residual cai
a 5. Um dividendo de 30 poderia demandar caixa acumulado ou dívida, apesar de
a receita não ter caído.

Em um contrato sintético que paga fluxo líquido de 20 por cinco anos, sem valor
residual, a 10%: VP=20×[1−(1,10)^−5]/0,10≈75,8157. A 12%, VP≈72,0955. Um
valor terminal de 200 ao fim do quinto ano adicionaria cerca de 124,1843 ao
primeiro cenário, superando o valor dos fluxos contratuais explícitos. Esse
contraste ilustra por que a hipótese de renovação pode dominar a avaliação.

## Dívida, índices e riscos compartilhados

Dívida indexada, prazo de amortização e custo de refinanciamento alteram a
distribuição. Uma razão dívida/EBITDA pontual não informa todo o risco de vencimento.
Contratos corrigidos por inflação podem oferecer proteção parcial, enquanto
custos, dívida e defasagem tarifária podem reagir em outro calendário. É preciso
construir a ponte do cenário econômico ao fluxo, não apenas rotular a empresa
como protegida de inflação.

Uma carteira com várias empresas elétricas pode manter risco regulatório comum,
além de riscos operacionais diferentes. A exposição setorial deve agregar os
pesos observados, deixando posições não classificadas em categoria própria.
Não se renormaliza a parcela conhecida para fazer o gráfico somar 100% quando
faltam cotações. Correlação histórica, se calculada, não elimina riscos de mudança
regulatória que ainda não apareceram na amostra.

## Aplicação e revisão no Nexo

Yield alvo pode simular distribuições, mas não comprova sustentabilidade de
concessão. Gordon exige uma justificativa adicional para estabilidade e horizonte.
DFC com contratos explícitos pode ser metodologicamente preferível, embora não
esteja automaticamente disponível no conjunto inicial de ferramentas.

Conserve identificação de cada concessão analisada, período das demonstrações,
notas de CAPEX, cronograma da dívida e fonte regulatória. Diferencie dinheiro
recebido de direitos contabilizados. Revise após decisões tarifárias, revisões
de investimento, eventos operacionais e alterações de contrato. A conclusão
deve dizer qual hipótese sustenta o preço teto e qual evento a invalidaria.

## Referências

- [ANEEL — exemplo de decisão sobre RAP e seu ciclo](https://www.gov.br/aneel/pt-br/assuntos/noticias/2025/estabelecida-a-receita-anual-permitida-rap-de-transmissoras-para-o-ciclo-2025-2026): referência para leitura de vigência, não taxa usada nos cenários.
- [CVM — dados e documentos dos emissores](https://www.gov.br/cvm/pt-br/acesso-a-informacao-cvm/perguntas-frequentes-da-cvm/como-acessar-dados-informacoes-sobre-regulados).
- Pontes de caixa e exemplos de contrato são criações sintéticas Nexo.
