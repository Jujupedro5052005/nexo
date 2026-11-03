# 09 — Fundos imobiliários

Versão 2.0 · referência técnica Nexo · revisão 03/11/2026.

## Direito econômico e segmentos

A cota de um FII representa participação no fundo, não propriedade direta de
uma fração livremente realizável de cada imóvel. Avaliação depende do regulamento,
da carteira, dos custos e da liquidez. Fundos de imóveis, recebíveis e fundos de
fundos não devem ser tratados como negócios idênticos. O segmento e a origem da
renda orientam quais informações precisam ser investigadas antes do parecer.

P/VP compara preço de mercado e valor patrimonial por cota, ambos em data e base
compatíveis. Um desconto pode refletir custos, risco de crédito, ativos difíceis
de vender ou avaliações patrimoniais atrasadas. Não prova que o patrimônio
poderá ser liquidado integralmente pelo valor contábil. O final "11" do ticker
também não é uma classificação confiável: existem outros valores mobiliários
com esse final. Ativo não classificado deve permanecer assim até haver evidência.

## Imóveis, contratos e vacância

Em fundos de imóveis, examine ocupação, locatários, concentração por imóvel,
prazo e tipo de contratos, revisões, carências e despesas do proprietário.
Vacância física mede área; vacância financeira depende da renda potencial. As
duas podem divergir muito quando os espaços possuem aluguéis diferentes.
Um prazo contratual longo não elimina crédito do locatário nem obrigações de CAPEX.

Exemplo sintético: prédio com 100 unidades de área, sendo 90 ocupadas. Vacância
física=10%. Se as 10 unidades vagas responderiam por 20 de uma renda potencial
de 100, vacância financeira=20%. Com receita efetiva=80 e despesas/CAPEX de 30,
sobram 50 antes dos demais itens. Usar apenas a vacância física ocultaria parte
da perda econômica. Não se deve extrapolar esse prédio para todo um segmento.

## Recebíveis, crédito e duration

Em fundos de papel, verifique devedor, garantias, subordinação, indexadores,
concentração, carência, amortização e inadimplência. Inflação alta pode aumentar
receita nominal de títulos indexados e, simultaneamente, alterar risco de crédito
e valor de mercado. Rendimento mensal elevado não implica ganho real elevado.
Retorno do principal e juros não são a mesma espécie de renda recorrente.

Duration resume sensibilidade a taxas sob hipóteses específicas. Para um
instrumento de duration modificada 4, um aumento de taxa de 1 ponto percentual
aproxima uma queda de 4% no preço, antes de convexidade e mudança de spreads.
O exemplo é uma aproximação sintética; não calcula duration de um FII inteiro
sem os fluxos, preços e indexadores de sua carteira.

## Exemplo de preço teto e qualidade da renda

Considere distribuição normalizada esperada de 8 por cota ao ano e yield alvo
de 10%. Referência=80; com desconto adicional de 15%, teto=68. Se 2 dos 8
resultarem de evento extraordinário e a hipótese recorrente cair a 6, a
referência passa a 60 e teto a 51. Essa diferença precisa aparecer antes de
concluir que uma cotação de 65 é atraente. Valores são sintéticos e brutos,
sem presumir a situação tributária do investidor.

Um fundo pode distribuir caixa de reserva em alguns períodos. Isso suaviza a
renda, mas não demonstra que o resultado recorrente acompanha a distribuição.
Compare rendimento e resultado, sazonalidade, ganhos de venda e amortizações.
Lucro contábil e FFO não são sinônimos; o provider precisa fornecer a definição
correta antes de usar um múltiplo. No conjunto inicial do Nexo, o método de
múltiplos para FII aceita VPA, não rebatiza LPA como FFO.

## Implementação e revisão

Registre fonte e competência do VPA, quantidade de cotas, data do preço,
janela de rendimentos, espécie dos eventos e indexador. Não misture dados
anteriores e posteriores a emissões sem ajustar a base. Um histórico de cota
sem rendimentos não é retorno total. Liquidez deve ser analisada em relação
ao tamanho da posição, sem inventar que o último preço está disponível para
todas as cotas que o usuário poderia querer vender.

O parecer deve declarar dados ausentes e revisar vacância, crédito, emissões,
concentração e distribuição. Uma conclusão favorável no cenário não supera
automaticamente limites de exposição da carteira. A interpretação continua
separada de qualquer execução de ordens, que não existe no copiloto.

## Referências

- [B3 — prospecto de FII com fatores de risco](https://www.b3.com.br/data/files/A6/B6/A1/53/7DA919104FE62719AC094EA8/Prospecto%20Definitivo.pdf): exemplo documental de riscos específicos, não regra de todos os fundos.
- [CVM — acesso a documentos e dados de fundos](https://www.gov.br/cvm/pt-br/acesso-a-informacao-cvm/perguntas-frequentes-da-cvm/como-acessar-dados-informacoes-sobre-regulados).
- Exemplos, equações aplicadas e roteiro de revisão originais Nexo.
