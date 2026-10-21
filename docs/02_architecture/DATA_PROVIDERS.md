# Provedores de dados — Incremento 06

Política atualizada em 21/10/2026: Yahoo público via yfinance é principal. A biblioteca não é afiliada ao Yahoo e não oferece SLA; dados são usados no contexto educacional/pessoal conforme seus termos. [Documentação yfinance](https://ranaroussi.github.io/yfinance/).

## Contratos e composição

Domain mantém `MarketDataProvider`, `FundamentalDataProvider`,
`DividendDataProvider`, `OfficialCompanyDataProvider`,
`OfficialFinancialStatementProvider` e `CorporateActionProvider` separados.
`main.py` recebe `ProviderServices` somente para composição/lifecycle e injeta
os contratos específicos na Application. Não existe provider financeiro universal.
O método legado de dividendos em FundamentalDataProvider permanece por
compatibilidade; a composição real injeta um DividendDataProvider independente.

Infrastructure contém HTTP, yfinance, datasets, caches e policies. Application
coordena análise/cadastro; Calculations mantém valuations e cross-check. UI só
apresenta snapshots imutáveis. Nenhuma integração altera Portfolio, Transaction,
Position. As novas tabelas de planejamento/metas/alertas são independentes das integrações e do ledger. Splits consultados não modificam o ledger.

## Routing definitivo

| Capability | Primary | Fallback |
|---|---|---|
| Search B3 | Yahoo | brapi → bolsai |
| Quote | Yahoo | brapi → bolsai (EOD) |
| History (todos os períodos) | Yahoo | brapi, se o período estiver disponível no plano |
| Fundamentals | Yahoo | brapi → bolsai → CVM se nenhum snapshot financeiro disponível |
| Dividends | Yahoo | brapi if enabled |
| Company registry | CVM | bolsai metadata |
| DFP/ITR | CVM | — |

Snapshot OHLCV segue Quote. Splits/actions seguem Yahoo, depois bolsai somente
com `NEXO_BOLSAI_ACTIONS_ENABLED=true`, confirmando acesso ao endpoint Pro.
Cadastro nunca usa bolsai como fonte oficial: seus metadados são o bridge de
identidade para a CVM. Pesquisa fallback usa `/companies`, nunca `/screener`.

Cada capability consulta Yahoo antes dos complementos, inclusive quando existe cache
válido de uma fonte complementar. Chamadas bem-sucedidas usam TTL; falhas repetidas
por ativo/operação usam cooldown de 30 s, invalidado pelo refresh. Consultas explícitas
podem tentar novamente sem apagar restrições de plano ou quotas remotas.

Cotação/fundamentos Yahoo compartilham `get_info` por 60 s, com proteção contra
consultas concorrentes. Fundamentals Yahoo usa LPA TTM, VPA do balanço mais recente,
receita/EBITDA TTM e razões normalizadas; exige moeda de negociação e contábil BRL.
Dados opcionais inválidos não derrubam uma cotação com preço/moeda válidos.

Complementos de fundamentos são consultados quando faltam LPA/VPA ou quando a
fonte prioritária está indisponível/vazia. Campos ausentes são preenchidos somente
com referência contábil idêntica e moeda compatível, preservando origem por campo
em `field_sources`; não se misturam trimestres desconhecidos/divergentes nem se
sobrescrevem valores Yahoo. Não há consulta paga automática para cada indicador
secundário ausente. P/L, P/VP, margens e alavancagem calculáveis localmente têm
prioridade sobre razões fornecidas por outra fonte.

CVM detalhada é opcional na análise (checkbox explícito). O fallback de fundamentos
CVM permanece apenas quando nenhuma fonte retorna entradas financeiras. O bridge
de identidade pode depender de bolsai; ausência da chave não impede análise Yahoo.

TTLs Yahoo adicionados: quote 60 s, search 900 s, fundamentals 12 h; history 1 h,
dividends/actions 12 h. O snapshot bruto é limitado ao processo e não é persistido.
Testar conexão em Configurações consulta Yahoo; providers complementares continuam
visíveis no diagnóstico local. Nenhuma chamada remota acontece ao abrir Configurações.

## Fontes e confiança

- **brapi:** mercado complementar. Política free deste incremento: 15.000 requests
  por ciclo, um ticker/request, histórico até três meses, aproximadamente 30
  minutos de atraso, dividendos desabilitados e fundamentos limitados. Batch
  default é 1; configuração maior exige capacidade compatível. Adaptador v2 e
  diagnósticos existentes são preservados.
- **bolsai:** fallback de fundamentos e metadados de companhia; cotação fallback
  representa fechamento diário/EOD. Header X-API-Key, sem chave em URL. Endpoints
  consumidos: companies, companies/{ticker}, fundamentals/{ticker},
  stocks/{ticker}/quote e corporate-events somente se habilitado. Informações
  de origem são mantidas; percentuais são convertidos em razões Decimal para
  apresentação compatível. Valores monetários publicados não são rescalados por
  suposição. P/L, P/VP e margens fornecidos servem como complemento quando o cálculo local falta; valuations
  próprios continuam em Calculations. Header X-RateLimit-Remaining é lido.
- **Yahoo/yfinance:** fonte principal de busca, cotações, fundamentos, histórico, distribuições de caixa e splits.
  B3 usa `.SA`. `auto_adjust=False` preserva fechamento informado (não uma série
  de retorno total). A biblioteca pode já ajustar preços por splits e fornece
  números de ponto flutuante; a fronteira converte para Decimal sem inventar
  precisão adicional. Não é fonte oficial de eventos B3.
- **CVM Dados Abertos:** cadastro e demonstrações oficiais exclusivamente por
  CSV/ZIP da CVM. Acesso público não exige API key.

Documentação consultada em 07/10/2026:
[bolsai](https://usebolsai.com/docs),
[cadastro CVM](https://dados.cvm.gov.br/dataset/cia_aberta-cad),
[DFP CVM](https://dados.cvm.gov.br/dataset/cia_aberta-doc-dfp),
[ITR CVM](https://dados.cvm.gov.br/dados/cia_aberta/doc/itr/DADOS/),
[yfinance history](https://ranaroussi.github.io/yfinance/reference/api/yfinance.Ticker.history.html).

## Identidade e CVM

companies/{ticker} normaliza ticker_primary, queried_ticker, tickers,
corporate_name, trade_name, cvm_code, cnpj, sector e status. A classe de ação
consultada precisa constar nos tickers. O bridge fica em
`data/cache/official/identities/`, TTL sete dias, e sobrevive a reinícios.
Sem bridge válido, retorna **identidade oficial não resolvida** antes de baixar
dataset. Não há fuzzy matching nem identificação por nome aproximado.

O cadastro completo é baixado uma vez e compartilhado entre companhias; os dois
identificadores devem corresponder. CSV Latin-1 separado por ponto e vírgula.
Cadastro, ZIPs anuais e timestamps ficam em `data/cache/official/cvm/`, ignorados
no Git. ZIPs são lidos por streaming; entradas não esperadas são descartadas,
sem extrair caminhos arbitrários para disco ou versionar datasets grandes.

Somente ITR do ano atual e DFP do ano atual/anterior quando necessário entram
no escopo. Não há download automático do histórico 2010/2011 em diante. A
consulta completa valida cadastro, tenta ITR e DFP atual, e usa DFP anterior
quando não há registro atual. O budget padrão de dois downloads pode fornecer
cadastro + ITR e deixar DFP indisponível até atualização explícita ou outro dia.
Falhas preservam datasets anteriores, sem apresentá-los como cache fresco.

OfficialFinancialStatement mantém CNPJ, código CVM, referência, relatório,
tipo de demonstração, código/nome da conta, valor, escopo, fonte, versão e
período do exercício. Escala MIL é convertida em reais; moedas/escalas não
suportadas são excluídas. Último exercício, última referência e última versão
vencem. Consolidado é preferido por tipo de demonstração; individual só entra
na ausência de consolidado daquele tipo. Nunca são somados. DRE com múltiplos
períodos atuais usa início mais antigo, preservando o YTD.

Fallback de fundamentos CVM fornece somente contas básicas inequivocamente
identificadas, com referência e origem oficiais; não inventa LPA, VPA, TTM,
EBITDA ou todos os indicadores. Cross-check técnico considera patrimônio,
ativos, receita e lucro por código **e** nome inequívocos e mesma referência.
Fluxos TTM agregados não são comparados com ITR YTD; comparação de fluxos exige
DFP anual. Divergência é exibida nos detalhes recolhíveis, sem bloquear UI,
substituir a fonte ou calcular média.

## Dividendos e Bazin

CashDividend mantém asset, event_type/kind, amount_per_share/amount, ex_date,
payment_date, moeda, fonte, verificação e limitações. Yahoo sem payment_date
retorna None. Tipo não distinguido entre dividendo/JCP permanece
`CASH_DISTRIBUTION`; não é convertido silenciosamente para DIVIDENDO/JCP.
DividendSummary identifica explicitamente `date_basis=ex_date` nessa origem.

Bazin recebe o DividendDataProvider normalizado. Para Yahoo, a soma usa data-ex
e distribuições de caixa reportadas, com a limitação visível. O seletor JCP não
consegue separar esses eventos; não há presunção de classificação oficial.
No fluxo legado/brapi, a janela continua por pagamento, exclui eventos futuros
e verified=False, e respeita seleção de JCP bruto. Datas ausentes não viram
datas de pagamento fictícias. Yield requerido permanece explícito.

Yahoo é a fonte operacional principal gratuita para proventos. CVM IPE não é parseado
automaticamente, pois os documentos não oferecem a estrutura necessária neste
incremento. B3CorporateEventsProvider é arquitetura futura, dependente de uma
interface pública estável; não há scraping B3. Alpha Vantage fica como opção
futura internacional, sem implementação ou configuração de outra chave.

## TTL, coalescing e desenvolvimento

| Fonte/operação | TTL |
|---|---:|
| brapi quote | 60 s |
| brapi search | 15 min |
| brapi history | 30 min |
| brapi fundamentals | 12 h |
| bolsai quote | 6 h |
| bolsai company | 7 dias |
| bolsai fundamentals | 12 h |
| Yahoo dividends | 12 h |
| Yahoo history | 1 h |
| Yahoo actions | 12 h |
| CVM cadastro | 24 h |
| CVM DFP/ITR | 24 h |

ProviderPolicy compartilha cache entre Ativos, Análises, Carteiras e Overview.
Memória é limitada a 512 entradas. Locks coalescem keys idênticas por operação
e também a decisão de routing com fallback; operações de ativos diferentes não
seguram o lock de rede umas das outras. Downloads CVM têm lock de dataset.
Invalidar versiona o cache para impedir repopulação por resposta anterior.
Não há polling/timer de mercado. Navegação reutiliza cache e DTOs.

`NEXO_PROVIDER_TEST_MODE=true` identifica desenvolvimento com cache-first estrito.
O routing também mantém cache-first fora desse modo; nenhum modo altera os TTLs
ou cria polling. Atualizações manuais invalidam apenas o cache solicitado.
O wrapper CachedMarketDataProvider anterior permanece compatível para os testes
e consumidores legados; seus defaults históricos não são usados na composição
real de 05.2. Os TTLs de produção estão centralizados em policy.py.

403 cria capability negativa por 12 h, compartilhada entre tickers. Invalidação
de dados não apaga restrição de plano. brapi dividends começa desabilitada;
ativação externa confirmada só permite fallback após Yahoo falhar. Falha de uma
capability não desabilita outra capability disponível do mesmo provider.

## Quotas e budgets locais

bolsai free: 200 requests/dia, reset 00:00 UTC. O header é a quota oficial
observada, diferente do contador local. Nunca se chama /keys/usage. Sem segredo
na URL, nos snapshots, no contador, no log ou nos painéis.

`data/provider_usage.json` registra dia UTC/provider/operação/quantidade de
tentativas remotas, inclusive respostas de erro. Escrita atômica e lock de
threads; pressupõe uma instância escritora desktop. Arquivo inválido ou falha
de persistência bloqueia rede em vez de resetar silenciosamente o contador.
Cache hit e capability negativa não reservam request. Yahoo conta operações de
ticker; yfinance pode executar múltiplos HTTP internos de sessão/consulta.

| Provider | Default local/dia | Configuração |
|---|---:|---|
| brapi | 100 | NEXO_BRAPI_SOFT_DAILY_BUDGET |
| bolsai | 40 | NEXO_BOLSAI_SOFT_DAILY_BUDGET |
| Yahoo | 50 | NEXO_YAHOO_SOFT_DAILY_BUDGET |
| CVM | 2 downloads | NEXO_CVM_SOFT_DAILY_BUDGET |

Exceder soft budget exige atualização explícita no escopo daquela operação de
worker. Isso não contorna plano, capability negativa ou HTTP 429 do serviço.
O botão Atualizar ativo invalida o cache uma vez antes de iniciar os workers e
propaga esse escopo explícito para cotação, histórico e análise. Fundamentos
usam brapi, depois bolsai em caso de erro ou resposta sem campos financeiros,
e por último CVM. Uma resposta parcial válida mantém sua fonte sem mesclar dados.
Enter/Buscar, seleção de resultado e troca de período também propagam o escopo
manual no respectivo worker, reutilizando cache válido. Consultas automáticas
mantêm o soft budget; nenhuma destas ações ignora limites remotos do serviço.
O header bolsai com remaining=0 bloqueia novas chamadas até o próximo dia UTC.

## UI e disponibilidade

Ativos apresenta snapshot: status/fonte, ticker/nome, preço, variação, cards
máxima/mínima/volume/market cap, horário do dado, consulta, latência e frescor.
None é “—”. EOD tem data de pregão sem horário artificial. A latência é duração
da consulta, jamais “tempo real”. A idade do timestamp na consulta é separada
do atraso estimado do plano; mercado fechado pode explicar dados mais antigos.
Detalhes recolhíveis apresentam JSON normalizado por lista explícita de campos,
sem raw headers, cookies ou credenciais. Gráfico fica abaixo e mostra origem.

Fundamentos mostram fonte própria e disponibilidade CVM; cadastro e contas
ficam nos detalhes oficiais. Splits exigem seleção explícita de consulta
adicional e aparecem nos detalhes, sem mutação financeira. Configurações mostra
quatro providers, papel, health, consumo, budget, restrições, hits, hit rate,
remaining quando informado e arquivos/datas CVM locais. Atualizar diagnóstico é
local. Estados: available, not configured, rate limited, plan restricted,
temporarily unavailable e offline; fonte configurada não é autenticação provada.

## Validação

pytest comum bloqueia transportes httpx, requests, curl_cffi e sockets; tentativa
falha mesmo se o adaptador capturar a exceção. Testes usam MockTransport,
DataFrames/factories fake e CSV/ZIP CVM pequenos. TTLs são testados com relógio
injetado sem reduzir a política real. Smoke online é script separado:

```powershell
python scripts/smoke_providers.py
python scripts/preview_snapshot.py
```

Smoke anuncia consumo máximo antes da primeira consulta: brapi 2, bolsai 2,
Yahoo 1 operação de ticker. CVM só lê cache válido e tem budget zero nesse script.
Uma consulta Yahoo fornece histórico e eventos; sem query adicional para cada
campo. Relatório sanitizado e captura ficam em tmp/ e não são versionados.
Não confundir fixture de sucesso com validação autenticada online.


## Incremento 07 — transporte Yahoo e cancelamento

O adaptador público padrão executa `get_info`, histórico e busca em processos
próprios, sem transmitir chaves pagas. O pai verifica cancelamento a cada 50 ms,
limita a consulta a 25 s e termina somente seu processo filho. Snapshot de 60 s
e coalescência continuam no pai; orçamento local é reservado antes da execução.
Factories de testes permanecem injetáveis, sem processo/rede real. Tokens de
tarefas canceladas impedem próximas reservas, inclusive de fallbacks. HTTP já
iniciado em brapi/bolsai/CVM ainda pode esperar timeout. Splits e informação de
ajuste são preservados nos históricos Yahoo para reconstrução do patrimônio.


## Correção de latência — Atualizar mercado — 21/10/2026

A atualização de carteiras usa `YahooFinanceProvider.get_quotes` com transporte
`quotes`: um processo, quatro workers de chart, metadados com preço/moeda/horário,
sem fundamentos. Cada SDK history usa timeout 6 s; o processo pai limita o lote
a 16 s e conserva resultados recebidos por mensagens intermediárias. Esperas de
complementos são adicionais e continuam sujeitas aos timeouts desses provedores.
`chartPreviousClose` não é usado como fechamento anterior do dia. Informações não
presentes ficam indisponíveis; `get_quote` individual conserva snapshot completo.

Routing reaproveita cache de cotações antes do lote e só complementa ativos
faltantes, com até quatro workers e cópia do contexto de budgets/cancelamento.
Publicação de cache por ativo ocorre sob o mesmo epoch do lote. Cache de uma fonte
complementar válida é aproveitado durante a falha recente Yahoo, sem nova consulta
imediata. A invalidação manual permite nova tentativa e preserva timestamps.
Contador local registra uma operação `quotes` por lote; isso não representa uma
única chamada HTTP ou quota oficial Yahoo. O SDK pode executar requisições internas.
