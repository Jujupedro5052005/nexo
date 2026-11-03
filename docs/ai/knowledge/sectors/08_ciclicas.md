# 08 — Empresas cíclicas e commodities

Versão 2.0 · referência técnica Nexo · revisão 03/11/2026.

## O ciclo modifica o denominador

Empresas expostas a petróleo, minério e outros insumos podem apresentar grandes
mudanças de resultado sem alteração proporcional de volume. A combinação de
preço realizado, câmbio, qualidade do produto, custos e capacidade produzida
determina a margem. Não é suficiente observar o preço internacional: descontos,
frete, royalties, hedge e mix podem afastar a receita efetiva do benchmark.

No topo de um ciclo, lucro elevado reduz P/L; no fundo, lucro pequeno ou negativo
eleva ou torna o indicador inaplicável. Ler esse movimento como barateamento
ou encarecimento automático inverte o problema. A investigação deve construir
um resultado normalizado ou cenários de preços e custos, mostrando quais etapas
são observadas e quais são estimadas.

## Modelo operacional sintético

Considere volume anual=10 unidades, preço realizado=8 BRL por unidade, custo
variável=4 e custo fixo=20. Receita=80; contribuição=40; resultado operacional
simplificado=20. Se preço cair 25% para 6, receita=60 e resultado=0. A queda de
25% no preço extinguiu 100% desse resultado, sem mudar volume ou custos.
Se preço subir para 10, resultado=40. Trata-se de alavancagem operacional,
não de uma probabilidade de retorno da ação.

Acrescente dívida líquida de 50 e necessidade de CAPEX de manutenção de 10.
O cenário fraco ainda precisa financiar obrigações, mesmo com resultado
operacional zero. Um dividendo pago no cenário forte não deve ser projetado
automaticamente no cenário fraco. Uma análise completa exigiria juros, tributos,
capital de giro e cronograma de produção; o exemplo exclui esses itens para
explicitar seu alcance, não para tratá-los como inexistentes.

## Normalização e custo econômico

Uma média de lucros só é útil se os anos forem comparáveis em capacidade,
participações e contabilidade. Aquisições, desinvestimentos e ramp-up mudam a
base. Reposição de reservas e manutenção de ativos são custos econômicos mesmo
quando não coincidem com a despesa contábil do período. Depleção, desmobilização
e obrigações ambientais também podem afetar valor.

Uma premissa de commodity de longo prazo deve explicar moeda, poder de compra,
fonte e critério. O modelo não cria cotação spot atual com base no treinamento
da IA. Se o Nexo não consultou um dado macro/commodity recente, a lacuna fica
registrada. Cenários ilustrativos podem variar entradas, sem serem chamados
de projeção de mercado ou consenso de analistas.

## Câmbio e dívida

Uma empresa exportadora pode ganhar receita em moeda forte e ter custos e
passivos em mais de uma moeda. Desvalorização local não é universalmente positiva:
depende dessa estrutura, de hedge e de preços relativos. Compare exposição
líquida e calendário. Dívida que parece pequena com EBITDA de pico pode tornar-se
elevada após compressão das margens; por isso, a cobertura deve ser reavaliada
nos cenários fracos, e não apenas na fotografia mais recente.

## Valuation e carteira

Múltiplos sobre lucro normalizado, fluxos explícitos e cenários operacionais
podem fornecer referências complementares. Yield alvo sobre provento excepcional
é particularmente frágil. Se os métodos discordam, explique se a divergência
vem de ciclo, CAPEX, distribuição ou desconto. Não selecione simplesmente o
maior valor calculado para apresentar uma oportunidade atraente.

Ter duas companhias de petróleo não garante diversificação do fator commodity.
Um parecer pode considerar evitar ampliar a posição por concentração, ainda
que o cenário base apresente desconto. O ganho acumulado do investidor não é
um fator suficiente para recomendar redução; a tese, o preço relativo e o peso
atual precisam participar da decisão.

## Implementação e revisão

Registre fonte de preço/câmbio, janela do lucro, capacidade e custos normalizados,
destino de CAPEX e premissas de distribuição. Apresente a sensibilidade separada
por variável antes de misturar vários choques. Não atribua probabilidades precisas
a cenários sem estimação estatística. Testes sintéticos devem confirmar a ponte
preço×volume−custos e rejeitar unidades incompatíveis. Os modelos operacionais
aqui descritos não são novas expressões executáveis do Gemini.

O parecer deve ser revisto após alteração de produção, política de preços,
investimentos, endividamento, governança ou condições do ciclo. Fontes primárias
do emissor são úteis para validar esses eventos; um documento metodológico antigo
não prova sua ocorrência atual.

## Referências

- [Petrobras — RI e central de informações ao mercado](https://www.investidorpetrobras.com.br/).
- [CVM — consulta a informações periódicas e eventuais](https://sistemas.cvm.gov.br/port/ciasabertas/menu4.asp).
- O modelo operacional e seus cenários são exemplos originais e sintéticos Nexo,
  sem dados atuais ou projeções atribuídas a Petrobras, Vale ou PRIO.
