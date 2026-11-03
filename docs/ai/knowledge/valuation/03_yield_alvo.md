# 03 — Preço teto por Dividend Yield alvo

Versão 2.0 · referência técnica Nexo · revisão 03/11/2026.

## Separar a identidade aritmética da decisão

Yield histórico é distribuição por ação numa janela dividida por um preço de
referência. Preço teto por yield é outra pergunta: qual preço satisfaz uma
exigência de distribuição esperada? P_teto=D_esperado/y_alvo. A fórmula é simples,
mas sua qualidade depende quase inteiramente do dividendo normalizado e da
justificativa do yield. Um valor alto de yield observado pode resultar de queda
de preço, pagamento extraordinário ou risco de corte. Não é um sinal automático
de oportunidade, nem substitui uma avaliação da capacidade de distribuir caixa.

O Nexo reutiliza o cálculo determinístico de Bazin existente. O nome não é
atribuído ao canal de vídeos e não implica que um único percentual seja adequado
a todas as empresas. O alvo é configurado pelo usuário ou explicitamente
identificado como uma hipótese de cenário, nunca como taxa garantida.

## Construir a janela e preservar a espécie

Antes de somar eventos, fixe início/fim, moeda, unidade por ação e critério de
data: pagamento, declaração ou data-ex. Somar uma fonte em pagamento e outra em
data-ex pode duplicar ou deslocar o mesmo direito. Deduplicação não pode usar
apenas a coincidência do valor: duas distribuições legítimas podem ser iguais.
Revisões e cancelamentos precisam de identificação e evidência documental.

Dividendos, JCP e eventos que uma fonte chama genericamente de distribuição em
dinheiro ficam separados. Não se presume a carga tributária pessoal do usuário.
JCP bruto não é automaticamente líquido. Um evento especial de venda de ativos
não demonstra renda recorrente. Se o provider não distingue a espécie, a análise
deve informar essa limitação; silêncio não é autorização para classificar.

Eventos futuros anunciados não são renda já recebida. Fluxos externos de mercado
também não creditam o livro-caixa do investidor. O documento metodológico serve à
avaliação por ação, mantendo separada a contabilidade da carteira.

## Exemplo sintético completo

Considere dividendos ordinários de 0,50 por trimestre, JCP bruto de 0,40 no ano e
dividendo especial de 1,00. A soma em dinheiro é 3,40, mas o dividendo recorrente
identificado no exemplo é 2,00. Com alvo de 8%, tetos seriam 42,50 e 25,00,
respectivamente. Confundir total passado com distribuição sustentável elevaria
o teto em 70%, sem mudança no negócio. A inclusão do JCP exige uma análise
separada e não autoriza inventar o rendimento líquido do investidor.

Para D_esperado=2,00, alvos 6%, 8% e 10% produzem 33,3333, 25 e 20. Um desconto
adicional de 20% leva os tetos finais a 26,6667, 20 e 16. Se cotação=22, o ativo
está abaixo do valor de 25 do cenário intermediário, mas acima do teto descontado
de 20. Esclarecer qual número recebe o nome de valor de referência e qual recebe
o nome de preço teto evita afirmações aparentemente contraditórias.

## Normalização e sustentabilidade

Uma janela de doze meses pode capturar sazonalidade, mas não um ciclo completo.
Uma mediana de anos comparáveis reduz a influência de um pico, sem garantir
o futuro. Todas as observações devem ser ajustadas para a mesma base por ação
antes de compará-las. Se um split dobra a quantidade e divide o preço, o dividendo
histórico por ação também precisa de base comparável; aplicar ajuste duas vezes
cria uma renda fictícia. O software deve preservar a política de ajustes da fonte.

Investigue payout, caixa operacional, reinvestimento, covenants e capital
regulatório. Quando essas verificações não estão disponíveis, o cenário pode
simular repetição da distribuição histórica, com uma ressalva específica:
sustentabilidade ainda não demonstrada. Não deve aparecer como previsão central
confiável apenas porque a aritmética é exata.

## Relação com Gordon e casos-limite

Gordon equivale a um yield de distribuição esperada igual a Ke−g, sob suas
hipóteses de crescimento constante. Um alvo de 8% não significa Ke=8% se há
crescimento, e a escolha do alvo isolado não especifica como ele é financiado.
Comparar ambos os métodos ajuda a identificar hipóteses incompatíveis, não a
escolher automaticamente o maior preço calculado.

Yield zero ou negativo é inválido. Dividendo ausente impede o cálculo; zero
explicitamente informado gera valor zero para aquele cenário, sem provar que a
empresa inteira vale zero. Moeda diferente da cotação impede comparação sem FX.
Pagamentos em ações, bonificações e amortizações exigem classificação própria.

## Implementação e revisão

Registre lista de eventos, critério de inclusão, janela, fonte, data de consulta,
tipo de distribuição, valor normalizado, alvo e desconto. Tests conhecidos
incluem 3/0,06=50, yield inválido, evento indisponível e cenário sem cotação.
Revise após mudança de payout, programa de investimentos, alavancagem ou política
de distribuição. Uma conclusão sobre aporte precisa também considerar o peso
da posição e a fragilidade do dividendo, não só o teto numérico.

## Referências

- [CVM — consulta a documentos de companhias](https://sistemas.cvm.gov.br/port/ciasabertas/menu4.asp): avisos, demonstrações e informações periódicas.
- [RI Petrobras](https://www.investidorpetrobras.com.br/): exemplo de fonte primária para verificar políticas e avisos de um emissor, sem importar valores atuais neste capítulo.
- Regras de janela, casos numéricos e protocolo de revisão são elaboração Nexo.
