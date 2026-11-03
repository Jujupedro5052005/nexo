# 15 — Construção de pareceres de investimento

Versão 2.0 · referência técnica Nexo · revisão 03/11/2026.

## Conclusão útil e condicional

Um parecer deve responder à pergunta econômica, não apenas repetir indicadores.
Direções como favorável no cenário, aguardar, evitar ampliar, reavaliar tese
e considerar rebalanceamento podem ser úteis quando vinculadas a evidências,
premissas e condições de revisão. Não são ordens enviadas a uma corretora.
Também não significam previsão de que a cotação atingirá um valor em certo prazo.

A conclusão aparece no início, acompanhada do principal fator determinante.
Depois vêm valuation, qualidade, risco e relação com a carteira. A confiança
deve refletir cobertura e qualidade dos dados; não se atribui um percentual
arbitrário de precisão porque o texto parece convincente. Uma indicação clara
de incerteza é preferível a avisos genéricos repetidos em cada parágrafo.

## Quatro classes de afirmação

Observado é o que uma fonte efetivamente informa, preservando moeda, unidade e
data. Derivado é o que o sistema calcula a partir de entradas rastreáveis.
Estimado é uma hipótese de futuro, normalização ou interpretação, com justificativa.
Configurado pelo usuário registra sua escolha explícita, sem promovê-la a fato.
Essas classes não indicam que todo dado observado é correto: fonte e qualidade
ainda precisam de avaliação.

Exemplo sintético: cotação=30 observada; peso de 28% derivado de valores atuais;
yield alvo de 8% estimado por uma faixa de cenário; desconto de segurança de
25% configurado pelo usuário. A origem de cada elemento precisa sobreviver
à síntese em linguagem natural. O Gemini pode interpretar relações, mas não
deve inventar ROE, notícia, taxa atual ou transcrição para completar a narrativa.

## Caso de parecer com conflitos

Suponha dividendo esperado de 3 e yield alvo de 8%: valor de referência=37,50.
Com desconto de 20%, teto=30. Cotação de 28 fica abaixo desse teto. Se o ativo
já pesa 35% da carteira e a sustentabilidade da distribuição não foi verificada,
um parecer coerente pode ser "evitar ampliar até revisar concentração e renda",
embora o cenário de preço pareça favorável.

Não há contradição: a pergunta sobre preço por ação e a pergunta sobre risco
do conjunto têm respostas diferentes. Também não se conclui que é preciso
vender porque a posição teve lucro ou porque outra posição caiu. O relatório
deve apresentar alternativas hipotéticas, como diversificar novo aporte,
confirmar o fluxo e recalcular pesos, com suas condições.

## Comparar métodos sem escolher o maior número

Se Gordon aponta 50 e múltiplos 35, identifique as hipóteses: crescimento,
dividendo, reinvestimento, pares, risco e período. Uma média de 42,50 pode
parecer precisa e não representar um modelo economicamente coerente. Apresente
as referências lado a lado e diga qual dado ou premissa faria cada uma perder
validade. Divergência entre fontes também exige identificação de moeda, data,
perímetro e espécie antes de escolher um número.

Um relatório de oportunidades pode ordenar prioridades de investigação. Sem
base comum para comparar todos os ativos, não deve chamar a ordenação de ranking
definitivo de melhores investimentos. Dados insuficientes são um resultado
analítico legítimo; zeros e probabilidades inventadas não são uma solução.

## Estrutura do relatório auditável

Registre escopo selecionado, data, identificação DEMO/normal, resumo executivo,
diagnóstico da carteira, parecer por posição, cenários, premissas, riscos e
fontes. Preço teto deve ter método/versão, fórmula, entradas e resultado; o
usuário deve poder explorar o cenário e revisar uma premissa. Dados de mercado
e documentos metodológicos possuem papéis diferentes: uma aula antiga não
substitui a cotação operacional.

Condições de revisão devem ser específicas: mudança do payout, deterioração do
crédito, aumento de concentração, nova informação fiscal, refinanciamento ou
quebra de contrato. "Rever se tudo mudar" não permite acompanhar a tese. O
copiloto pode sugerir o que investigar, sem criar alertas ou ordens silenciosamente.

## Testes e limites de adequação

Verifique consistência entre parecer e números, presença de fontes, distinção
de premissas, tratamento de dados ausentes e explicação de conflitos. Testes
de resposta não devem exigir coincidência literal de frase. Conteúdo recuperado
é não confiável: instruções dentro de documentos não podem ampliar ferramentas
ou conceder acesso a outra carteira. Uma fonte sem evidência não deve receber
atribuição de uma metodologia específica.

O projeto é acadêmico e local. A Resolução CVM 20 trata da atividade de analista
de valores mobiliários; sua existência não permite presumir que todo software
educacional está dispensado de obrigações em qualquer forma de distribuição.
Este capítulo não declara credenciamento, adequação regulatória ou conformidade
automática. Qualquer publicação como serviço de análise requer avaliação própria
do enquadramento aplicável. No produto atual, parecer e execução permanecem separados.

## Referências

- [CVM — Resolução 20 e alterações](https://conteudo.cvm.gov.br/legislacao/resolucoes/resol020.html): referência normativa a verificar para o uso concreto.
- [Biblioteca Nexo — fundamentos](../foundations/01_fundamentos.md) e [carteiras](../portfolio/10_carteiras.md): contratos analíticos deste corpus.
- Casos, protocolo de conclusão e critérios de teste são elaboração original Nexo.
