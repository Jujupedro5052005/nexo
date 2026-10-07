# Análises, fundamentos e comparação — Grande Incremento 05

## Fontes e contratos

`FundamentalDataProvider` é uma ABC separada de `MarketDataProvider`, com apenas
get_fundamentals e get_dividends. A Application depende desses contratos; a UI
recebe AssetAnalysis/ComparedPortfolio. BrapiMarketDataProvider implementa ambos,
reutilizando o httpx.Client e a fronteira de erros/JSON Decimal do incremento 04.
Sem scraping, endpoint legado, outra API, ORM analítico ou repository derivado.

Fontes oficiais verificadas em 06/10/2026:

| GET utilizado | Parâmetros | Base oficial |
|---|---|---|
| /api/v2/stocks/statistics | symbols, mode=current | [Estatísticas](https://web-next.brapi.dev/docs/acoes/estatisticas) |
| /api/v2/stocks/financial-data | symbols, mode=current | [Dados financeiros](https://web-next.brapi.dev/docs/acoes/dados-financeiros) |
| /api/v2/stocks/dividends | symbols, startDate, endDate, sortOrder=asc | [Proventos](https://web-next.brapi.dev/docs/acoes/dividendos) |

Cotação, catálogo e histórico v2 existentes são reutilizados. Estatísticas e dados
financeiros atuais fornecem métricas de 12 meses e saldos disponíveis. Não se
misturam DRE anual e balanço trimestral para inventar um indicador TTM. Balanço,
DRE e dictionary foram investigados para validar contrato/unidades, mas não são
consultados pelo produto. [Dicionário](https://web-next.brapi.dev/docs/dicionario)
identifica campos monetários B3 em BRL; financialCurrency ausente segue esse
contrato. Se explicitamente estrangeira, o módulo financeiro é descartado com
aviso; estatísticas válidas permanecem. Quote estrangeira nunca entra em múltiplos,
DY ou margem contra preço calculado BRL. É um escopo B3/BRL, sem conversão cambial.

Dados nullable permanecem None. Um campo inválido não descarta os outros;
falha de um dos dois módulos preserva o módulo disponível com origem/motivo.
Ambos indisponíveis causam erro seguro de mercado. Ticker alterado é rejeitado.
Acesso/limites dependem da API/plano; token externo opcional não é logado.

## Modelos e indicadores

CompanyFundamentals é snapshot imutável: Asset, Decimal opcionais, moeda BRL,
referência contábil opcional, UTC de consulta, fonte e avisos. CashDividend contém
pagamento, valor por ação, tipo e verified opcional. DividendSummary contém janela,
eventos, moeda/fonte/consulta. Sem persistência. Indicator preserva valor, unidade,
fórmula, origem e motivo de indisponibilidade.

| Indicador | Fórmula/base | Origem exata |
|---|---|---|
| LPA (12M) | Lucro por ação informado pelo provider; não recalculado | statistics.trailingEps, fallback earningsPerShare |
| VPA | Patrimônio líquido / ações, informado | statistics.bookValue |
| P/L | Preço BRL / LPA positivo | Quote.price + LPA |
| P/VP | Preço BRL / VPA positivo | Quote.price + VPA |
| DY da janela | Proventos selecionados por ação / preço BRL positivo | dividends.rate/paymentDate + Quote.price |
| ROE informado (12M) | Lucro líquido / patrimônio, base do provider | financial-data.returnOnEquity |
| ROA informado (12M) | Lucro líquido / ativos, base do provider | financial-data.returnOnAssets |
| Margem líquida informada | Lucro líquido / receita, base do provider | financial-data.profitMargins |
| Margem EBITDA calculada | EBITDA / receita positiva, módulo atual | financial-data.ebitda / totalRevenue |
| Dívida líquida / EBITDA | (Dívida total − caixa) / EBITDA positivo | financial-data.totalDebt, totalCash, ebitda |

ROE/ROA/margens são frações (0,20 = 20%), multiplicadas por 100 apenas na
apresentação. ROE/ROA/margem líquida são informados, não reconstruídos com uma
DRE incompatível. Dívida/caixa exigem valores não negativos; caixa líquido pode
produzir índice negativo legítimo. Denominador ausente/nulo/não positivo produz
None; valores negativos válidos de lucro/ROE não são zerados. DY zero é legítimo
somente quando uma janela válida não contém eventos selecionados positivos.

## Política de proventos e premissas

Janela inclusiva: dia seguinte à data equivalente do ano anterior até data UTC
atual, com política explícita para 29/02. Exemplo: 07/10/2025 a 06/10/2026.
Usa paymentDate, não aprovação/ex-date, e rate ajustado por ação da API. Não
reconstitui o que o investidor efetivamente recebeu, impostos ou eventos de ações.

Padrão visível: somente DIVIDENDO; checkbox opcional inclui JCP bruto, sem imposto.
Futuros e verified=False são excluídos; verified ausente segue disponibilidade do
provider, sem afirmar auditoria. RENDIMENTO, stockDividends e subscrições não
entram nessa política. Se um evento elegível tem data/valor inválido, todo o total
fica indisponível; não se omite silenciosamente para apresentar soma incompleta.
Um rate inválido em evento comprovadamente fora da janela não contamina a janela.

Graham = sqrt(22,5 × LPA × VPA), ambos Decimal finitos e estritamente positivos.
Sem esses inputs, nenhuma estimativa. Não usa módulo, fallback zero ou patrimônio
inventado. Bazin = proventos selecionados da janela / yield requerido. Yield é
entrada explícita percentual na UI (6 → 0,06), positiva, sem padrão oculto; janela
sem proventos positivos não gera preço Bazin. Não projeta crescimento de dividendos.

Margem: diferença = preço calculado − preço atual; percentual = diferença / preço
calculado, exigindo preço calculado positivo e mesma moeda BRL. Pode ser negativa.
UI descreve preço acima/abaixo/igual ao valor calculado, sem comprar/vender, ranking
recomendado ou recomendação financeira automática. Aviso educacional discreto.

## Risco do histórico do ativo

Retorno diário r_i = close_i / close_(i−1) − 1. Volatilidade diária = desvio padrão
amostral dos retornos (denominador n−1); pelo menos 3 fechamentos estritamente
cronológicos. Anualização = volatilidade diária × sqrt(252), premissa de pregões
explícita na UI. Drawdown máximo = min(close_i / pico_acumulado_i − 1), pelo menos
2 fechamentos. Série constante/crescente pode ter drawdown zero legítimo.

Fonte/período/consulta são identificados. Close pode ser ajustado pela API; não há
reinvestimento próprio de proventos nem série de patrimônio/carteira. Amostra curta,
lacunas de pregões e qualidade do provider limitam interpretação; 252 é hipótese,
não promessa de performance. Nenhum Sharpe sem taxa livre de risco/frequência.

## Carteiras e concentração

ComparePortfolios exige pelo menos dois IDs distintos existentes; nome não é
chave. Cada carteira é reconstruída do seu ledger. Uma chamada execute_many
compartilha batch deduplicado entre todas. Métricas: posições/contagem de operações,
custo remanescente, valor aberto, realizado inclusive encerradas, não realizado,
resultado total e retorno não realizado / custo aberto. Sem benchmark inventado.

Pesos w_i = valor atual BRL da posição / soma dos valores abertos BRL. Exigem
valuation completo e soma positiva. Maior = max(w_i), top 3 = soma dos três maiores,
HHI = soma(w_i²), em escala 0–1, sem score/limiar arbitrário: um ativo tem HHI 1,
N pesos iguais têm HHI 1/N. Valores são ordenados por peso e ticker nos empates.

Falta/FX em qualquer posição mantém custo/realizado e preços válidos individuais,
mas deixa agregado e todos os pesos/concentrações indisponíveis, com tickers/motivo.
Não se normaliza a parte disponível como se fosse toda a carteira. Sem posições,
valor aberto zero é legítimo; percentual e concentração não têm denominador.
Overview/Carteiras usam o mesmo modelo, sem regras duplicadas. A antiga alocação
por categoria demo foi removida do Overview; distribuição real é por ativo.

## Performance temporal: decisão deliberada

Retorno aberto sobre custo é uma fotografia das posições restantes; realizado +
não realizado é resultado monetário. Nenhum deles é chamado de rentabilidade
histórica, TWR, XIRR/MWR, patrimônio total ou retorno de toda a carteira.

TWR não implementado: ledger BUY/SELL não representa aportes/retiradas externos,
não há caixa e faltam avaliações completas imediatamente nos limites de fluxo.
Não usar compras/vendas como fluxos externos. XIRR/MWR indisponíveis pelo mesmo
problema de fluxos; benchmark indisponível sem série confiável e comparável.

Desenho futuro (não implementado): modelar explicitamente caixa e aporte/retirada
com data, moeda e identidade; registrar política de taxas/proventos/eventos;
reconstruir patrimônio completo e avaliar antes/depois de cada fluxo externo.
A camada calculations calcularia retorno de cada subperíodo e TWR = produto(1+r)
− 1, com denominadores positivos e cobertura completa. Application coordenaria
fluxos/avaliações; UI só apresentaria séries e limitações. Requer requisito próprio,
migração deliberada e testes de fluxo/tempo/moeda, sem inferência a partir de trades.

## Cache, coordenação e UI

CachedMarketDataProvider compõe os dois contratos com um mesmo adapter/client.
Cache em memória limitado a 256 entradas (remoção da mais antiga ao exceder),
TTL monotônico: quote 30s; history 300s; fundamentals/dividends 300s. Chaves incluem
Asset, período ou janela. Erros não são armazenados; snapshots parciais válidos
mantêm seus avisos até TTL/refresh. Chamadas em voo da mesma chave são coalescidas;
quotes faltantes são solicitadas em lote. Busca não é cacheada. Sem polling/tabela.

Atualizações manuais invalidam o ativo ou todo o cache. Época de invalidação impede
resposta anterior em voo de repovoar cache novo. Workers Qt recebem casos de uso;
sinais enfileirados entregam modelos na GUI. Gerações descartam resultados após
mudança de ticker, período, yield, política JCP ou seleção de carteiras. Registro
invalida comparação e valuation local; quotes válidas podem continuar até TTL.
Ativos invalida antes de iniciar suas consultas paralelas. Fechamento espera workers
antes de fechar client/engine; cancelamento HTTP instantâneo não implementado.

Ativos e Análises compartilham AssetAnalysisPanel e o cache. Análises possui tabs
para ativo e carteiras. Fonte, referência contábil e consulta são separadas; ausência
contábil não ganha data inventada. Valores monetários/múltiplos são formatados em
2 casas na UI, sem arredondar o modelo. Tooltips preservam fórmula/origem completa.
Demo remanescente: evolução histórica de carteira, benchmarks, insights, caixa,
metas, alertas, planejamento e relatórios. Não existe fallback demo analítico.

## Verificação

tests/analytics cobre fórmulas/invariantes, respostas reais controladas por
MockTransport, dados parciais/FX, política de proventos, TTL/deduplicação/coalescência/
invalidação durante voo, comparação por ID, SQLite e contexto/heartbeat Qt.
Suíte normal não usa rede ou banco do usuário. Evidências atuais e roteiro integrado
em [TESTING.md](../04_development/TESTING.md) e
[CURRENT_STATUS.md](../06_progress/CURRENT_STATUS.md).
# Atualização 05.2

Fundamentos bolsai mantêm indicadores diretos e origem própria. CVM fornece
cadastro/demonstrações/raw fallback; cross-check conservador fica em Calculations.
AnalyzeAsset recebe DividendDataProvider separado. Yahoo preserva tipo de
distribuição de caixa não distinguido e payment_date=None; Bazin identifica
janela por data-ex e limitações. A política de pagamento brapi descrita abaixo
permanece no fluxo legado. Routing/TTLs atuais:
[DATA_PROVIDERS.md](DATA_PROVIDERS.md).

