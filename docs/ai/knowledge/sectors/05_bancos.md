# 05 — Análise fundamentalista de bancos

Versão 2.0 · referência técnica Nexo · revisão 03/11/2026.

## A economia do intermediário

O banco transforma prazos, liquidez e risco de crédito. Depósitos e outras formas
de captação fazem parte de sua operação; não podem ser analisados simplesmente
como a dívida de uma indústria. A qualidade do balanço e o capital disponível
influenciam a capacidade de crescer e distribuir. Por isso, modelos de equity
e relações entre retorno e patrimônio são úteis, desde que não se confunda
patrimônio contábil com valor de liquidação garantido.

ROE é lucro atribuível ao acionista dividido pelo patrimônio correspondente,
idealmente médio quando se mede fluxo sobre um estoque. ROA usa ativos como base.
A comparação exige consistência de período, conglomerado e ajustes. Uma elevação
de ROE por redução temporária de capital não tem o mesmo significado que melhora
de rentabilidade recorrente. Lucro ajustado divulgado pelo emissor precisa ser
conciliado com o reportado, especialmente em períodos de provisões relevantes.

## Crédito, eficiência e capital

Examine composição da carteira, atrasos, renegociações, perdas reconhecidas,
cobertura de provisões e concentração por segmento. Um saldo de inadimplência
baixo não basta se há crescimento rápido de concessões ou mudanças de classificação.
Eficiência operacional deve ser calculada segundo a definição divulgada; menor
razão de despesa/receita pode coexistir com deterioração do custo de crédito.
Receita de serviços, margem financeira e resultado de tesouraria têm perfis distintos.

Capital regulatório limita distribuição e expansão. Patrimônio líquido contábil,
capital principal e índices prudenciais não são sinônimos. Não se compara um
indicador individual a outro de conglomerado sem reconciliar escopo. O IF.data
do Banco Central é uma fonte primária para investigação de informações contábeis
e de capital; disponibilidade no portal não significa que esses dados já tenham
sido coletados pelo provider do Nexo.

## Derivação do retorno excedente estável

Suponha VPA inicial B0, ROE constante R, custo próprio K e crescimento g do
patrimônio. Com clean surplus e sem emissões, lucro do próximo período é R×B0,
retenção necessária é g×B0 e distribuição potencial é (R−g)×B0. Aplicando
Gordon ao fluxo potencial constante em crescimento, V0=B0(R−g)/(K−g).
Equivalentemente, V0=B0+B0(R−K)/(K−g): patrimônio mais valor presente do retorno
excedente. Isso não é uma previsão da cotação e exige K>g e crescimento financiável.

ROE≥g evita distribuição negativa no estado assumido, mas não demonstra que o
modelo seja apropriado a qualquer banco. Se R=K, P/VP justo do cenário é 1;
se R>K, há prêmio sob essas hipóteses; se R<K, há desconto. Não se pode usar
um ROE excepcional de um trimestre como retorno perpétuo sem investigação.

## Caso sintético e sensibilidade

Para VPA=20 BRL, ROE=18%, K=14% e g=3%, V=20×0,15/0,11≈27,2727; com
desconto de 20%, teto≈21,8182. O P/VP correspondente é aproximadamente 1,3636.
Se K subir a 16%, com as demais entradas fixas, V≈23,0769 e teto≈18,4615.
Se ROE cair a 14%, mantendo K=14%, V=20 e teto=16. A hipótese sobre a
rentabilidade sustentável é economicamente tão importante quanto o desconto.

No Nexo, taxas de uma faixa ilustrativa ou propostas pelo Gemini são classificadas
como estimadas. VPA e ROE são observados somente com fonte/período; uma razão
derivada mantém a memória de cálculo. Sem esses dois indicadores, não se executa
o modelo preenchendo os campos com médias inventadas. O resultado é uma análise parcial.

## Decisão e riscos não capturados

Um banco aparentemente descontado pode estar exposto a deterioração de crédito,
funding caro, risco operacional, judicialização ou restrições de capital. A
comparação com pares deve incluir esses fatores, e não apenas o P/VP. A conclusão
"favorável no cenário" depende de confirmação das hipóteses e da concentração
da carteira. Reduzir exposição pode fazer sentido para o conjunto mesmo quando
o cenário por ação é atrativo; a aritmética não executa a negociação.

O motor valida VPA positivo, parâmetros finitos, K>g e limites de precisão. Há
testes independentes para R=K, prêmio, desconto e K=g. Na revisão, procure
mudanças de qualidade da carteira e da política de capital. Uma atualização de
cotação não atualiza automaticamente o trimestre do ROE, e ambas as datas precisam
ser apresentadas. Não há atribuição deste método a vídeo que não foi processado.

## Referências

- [Damodaran — Valuing Financial Service Firms (2009)](https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/finfirm09.pdf): especificidades da avaliação de instituições financeiras.
- [Banco Central — IF.data](https://www3.bcb.gov.br/ifdata/): fonte primária de investigação prudencial e contábil.
- [Banco do Brasil — Relações com Investidores](https://ri.bb.com.br/) e [Itaú — RI](https://www.itau.com.br/relacoes-com-investidores/): demonstrações e explicações dos emissores, sem números atuais importados aqui.
- Derivação, exemplo e limites de implementação são elaboração original Nexo.
