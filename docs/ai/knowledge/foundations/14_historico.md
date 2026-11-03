# 14 — Análise histórica e comparação de empresas

Versão 2.0 · referência técnica Nexo · revisão 03/11/2026.

## Uma série não é apenas uma lista de números

Cada observação precisa de entidade, conceito, unidade, moeda, período e versão.
Uma sequência de preços diários não é uma sequência de fundamentos trimestrais.
Data de consulta não é data efetiva, e data de publicação pode ser posterior
à competência contábil. Um backtest que usa uma demonstração antes de ela se
tornar pública incorpora informação futura, mesmo quando os cálculos estão corretos.

Provedores podem revisar períodos anteriores. O histórico utilizado deve ser
identificável para que uma análise possa ser reproduzida. Não se afirma possuir
evolução de fundamentos quando a API oferece apenas o snapshot mais recente.
O Nexo mostra o histórico de cotações disponível e declara essa diferença.

## Eventos societários e bases por ação

Splits, grupamentos, bonificações, subscrições e mudanças de ticker afetam a
comparabilidade. Um split de duas para uma transforma preço 100 em 50 e dobra
quantidade; não significa perda de 50%. Uma série ajustada pode tratar esses
eventos, mas o aplicativo precisa saber o ajuste já aplicado para não repeti-lo.
Eventos do ledger só mudam posições mediante o fluxo confirmado existente.

Exemplo sintético: antes do split, 10 ações a 100 valem 1.000; depois, 20 a 50
continuam valendo 1.000. Dividendo por ação anterior de 4 corresponde a 2 na
nova base. Comparar 4 antigo a 2 novo sem ajuste sugeriria um corte inexistente.
O mesmo princípio vale a lucro e patrimônio por ação, respeitando regras de
divulgação e diluição apropriadas.

## Retorno de preço e retorno total

Uma cotação que cai de 100 para 98 após distribuição de 5 possui retorno de
preço de −2%. Um retorno total simplificado do período, sem custos/impostos,
é (98+5)/100−1=3%. Uma série que já reinveste distribuições não pode receber
esse dividendo novamente. O significado de adjusted close deve ser verificado
na fonte; o nome de um campo sozinho não é uma prova de política de ajuste.

Performance da carteira envolve também fluxos e caixa. Somar as séries dos
ativos com quantidades de hoje aplica as posições atuais ao passado e pode
produzir uma trajetória que o investidor nunca teve. A reconstrução deve
usar quantidades históricas e eventos, preservando as limitações documentadas
do sistema. Gráfico do ativo não recebe rótulo de patrimônio real.

## Comparabilidade contábil

Resultados anuais, trimestrais isolados e acumulados no ano têm relações
distintas. Somar quatro acumulados trimestrais conta partes do mesmo lucro
várias vezes. Uma base TTM coerente pode combinar último anual com acumulado
atual e retirar acumulado do mesmo período anterior, respeitando versões e
consolidação. Esse procedimento exige as três informações correspondentes,
não apenas uma aproximação com dados de outra empresa.

Moeda, perímetro de consolidação, efeitos não recorrentes e mudanças de norma
também importam. Ajustar lucro deve produzir uma ponte entre valor reportado
e normalizado, sem excluir arbitrariamente perdas. Uma aquisição pode elevar
receita sem representar crescimento orgânico. A interpretação precisa seguir
as notas e o escopo, não apenas a inclinação do gráfico.

## Alinhamento e amostras

Para comparar retornos de duas empresas, alinhe por datas compatíveis, não
pela posição das linhas. Não preencha uma série faltante com zero, pois isso
introduz artificialmente dias sem variação. Um número pequeno de observações
ou uma sequência constante pode impedir estimativas úteis de correlação.
Informação insuficiente deve produzir resultado ausente com motivo.

Seleção de empresas sobreviventes pode excluir companhias que saíram do mercado;
uma comparação histórica precisa considerar esse viés. Os pares de hoje não
são necessariamente os pares disponíveis na data passada. Esses limites devem
ser apresentados sem inventar correções empíricas que o software não executa.

## Implementação e revisão

Armazene timestamps com fuso quando a fonte os fornecer, preserve datas sem
horário como datas e não invente fechamento intradiário zero. Uma fonte que
não oferece horário efetivo deve ser rotulada assim, sem usar a hora da consulta
como substituto. Testes devem cobrir split sintético, datas divergentes, ausência
de pontos, moeda e comparação com série constante.

O relatório precisa permitir abrir a evidência original sob demanda. A visão
principal arredonda números para leitura, mas o diagnóstico preserva precisão
e origem. Uma revisão futura pode então distinguir mudança econômica de mudança
de fonte, ajuste ou versão.

## Referências

- [CVM — informações periódicas e eventuais](https://sistemas.cvm.gov.br/port/ciasabertas/menu4.asp).
- [CVM — acesso a dados públicos de regulados](https://www.gov.br/cvm/pt-br/acesso-a-informacao-cvm/perguntas-frequentes-da-cvm/como-acessar-dados-informacoes-sobre-regulados).
- Casos de eventos e retorno total são exemplos matemáticos sintéticos Nexo;
  não reproduzem a performance de uma carteira do usuário.
