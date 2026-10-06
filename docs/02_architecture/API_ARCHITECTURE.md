# Integração de mercado — Grande Incremento 04

## Provider e fontes oficiais

A brapi é o provider inicial para B3. Documentação oficial consultada em
06/10/2026; smoke online sem token confirmou cotação, busca e histórico. Dados
observados não estão hardcoded no produto e não são fixtures da suíte comum.

Base centralizada: `https://brapi.dev`. Adapter: `infrastructure/market_data/adapters/brapi.py`.

| Operação | Endpoint GET | Parâmetros utilizados | Documentação |
|---|---|---|---|
| Quotes | `/api/v2/stocks/quote` | symbols em lote | [Cotação](https://web-next.brapi.dev/docs/acoes/cotacao) |
| Busca | `/api/v2/tickers` | search, limit=20, sortBy=symbol, sortOrder=asc | [Tickers](https://web-next.brapi.dev/docs/tickers) |
| Histórico | `/api/v2/stocks/historical` | symbols, range=1mo/3mo/1y, interval=1d, sortOrder=asc | [Histórico](https://web-next.brapi.dev/docs/acoes/historico) |

Os endpoints v2 entregam `results`; quote/histórico usam envelope por ativo
com requestedSymbol, symbol e data. Renomeações/conversões sinalizadas não são
aplicadas silenciosamente à quantidade original do ledger: retorno indisponível.
Fechamento histórico é o `close` informado pela API e pode ser ajustado; não é
uma série de patrimônio nem um cálculo de dividendos.

## Fronteiras

```text
UI -> TaskRunner (QRunnable/QThreadPool) -> casos de uso Application
Application -> MarketDataProvider (ABC em Domain)
MarketDataProvider <- BrapiMarketDataProvider -> httpx -> API
LoadPortfolioValuation -> LoadPortfolioPositions -> ledger SQLite
LoadPortfolioValuation -> calculations/valuation -> PortfolioValuation
```

GetAssetQuote, SearchAssets e GetAssetHistory conhecem somente o contrato.
LoadPortfolioValuation.execute_many reconstrói as carteiras, deduplica todos os
ativos abertos, obtém o mesmo batch e calcula snapshots imutáveis. Cálculos não
fazem HTTP/SQL. main.py injeta implementações concretas. Domain não importa
httpx/Qt/ORM; Application não importa brapi/httpx; UI não acessa banco/API.

## Modelos e Decimal

Quote inclui Asset, price, currency, nome, change/change_percent opcionais,
market_time opcional, retrieved_at e source. HistoricalPrice inclui timestamp,
close e OHLC/volume opcionais. PriceHistory agrega pontos cronológicos/período e
fonte; AssetSearchResult representa catálogo, sem tabela Asset.

`json.loads(..., parse_float=Decimal)` lê o literal decimal JSON diretamente;
inteiros/strings numéricas também são convertidos na fronteira. Não há passagem
por float nem quantize financeiro. Rejeitam-se preços não positivos, não finitos,
metadados inválidos e horários de mercado sem offset. Datetimes Unix viram UTC;
ISO mantém offset. retrieved_at usa UTC. Float ocorre somente na coordenada dos
gráficos Qt, após cálculos Decimal. Formatação monetária em duas casas é visual.

## Autenticação, limites e falhas

BRAPI_TOKEN opcional em ambiente ou `.env`; BRAPI_API_KEY é alias. Ambiente tem
prioridade sobre `.env`. Token fica no header Authorization: Bearer, nunca URL,
repr de settings, erro ou log. `.env*` é ignorado, com exceção de `.env.example`.
[Autenticação oficial](https://web-next.brapi.dev/docs/authentication).

Sem token, quotes/histórico são permitidos para PETR4, VALE3, ITUB4 e MGLU3;
outros ativos recebem falha de acesso local sem bloquear os públicos. A busca
consulta catálogo sem exigir token. Com token, permissões e limites dependem do
plano. BRAPI_BATCH_SIZE controla chunks, padrão 5, faixa 1–100; configure conforme
seu plano. API pode recusar lote/período. Não há fallback para endpoint legado.

Timeout explícito: 10s por operação de rede, não prazo total de todos os lotes.
401/403 viram MarketAuthenticationError; 429 MarketRateLimitError; 404
AssetNotFoundError; transporte/status/JSON inválido MarketDataUnavailableError.
Sem retry automático/polling. QuoteBatch retém quotes válidas e QuoteIssue por
ativo. Falhas não expõem corpo de resposta, stack ou credencial.

## Valuation e moedas

O custo do ledger atual é BRL. Para cada posição BRL com cotação válida:

```text
market_value = quantity × price
unrealized_profit_loss = market_value - cost_basis
unrealized_return = unrealized_profit_loss / cost_basis (cost_basis > 0)
invested_cost = soma dos custos remanescentes abertos
realized_profit_loss = soma realizada de posições abertas + encerradas
total_profit_loss = realized_profit_loss + unrealized_profit_loss
```

Retorno percentual é somente o não realizado sobre custo aberto, exibido ×100;
não há rentabilidade total percentual ou denominador fictício. Não realizado
agregado = valor de mercado das posições abertas - custo aberto. Não é patrimônio
total: caixa, aportes, retiradas e proventos ainda não existem.

Quote ausente mantém custo/realizado e usa None nas métricas dependentes. Quotes
parciais continuam visíveis nas linhas; agregado de mercado/resultado total fica
indisponível se qualquer posição não puder ser valorada em BRL. Moeda estrangeira
mostra preço e valor na moeda própria; não há conversão ou P/L contra BRL.
Carteira sem posições abertas tem valor aberto/não realizado matematicamente
zero, mantém realizado de posições encerradas e não apresenta percentual sem
base de custo. Contexto Decimal local com mínimo 50 dígitos e precisão ampliada
pela magnitude/escala; não depende do contexto global.

## Concorrência, refresh e temporalidade

TaskRunner em ui/workers.py encapsula QRunnable/QThreadPool com duas threads por
runner. Worker devolve modelo/erro via sinal enfileirado; QObject receptor aplica
somente na thread GUI. IDs de geração descartam respostas antigas ao trocar
carteira, ativo, busca ou período. Registro de transação invalida valuation.

Carregamento inicial/de contexto e refresh manual; sem timer agressivo. O app
não tem cache de provider/TTL/persistência. Reutiliza a última fotografia visual
no mesmo contexto para evitar HTTP ao alternar páginas; refresh força consulta.
A UI informa source, instante consultado e referência de mercado separadamente,
inclusive se a API omitir market_time. Esse horário não garante tempo real.
Fechar suprime callbacks e limpa tarefas pendentes; tarefas em execução terminam
sob timeout, antes de fechar client/engine. Não há cancelamento HTTP instantâneo.

## UI, offline e escopo

Ativos: busca real, seleção, preço/moeda/variação, período, histórico e gráfico de
fechamento real. Falha limpa série/cotação anterior; sem dados demo de fallback.
Carteiras: custo/realizado locais, valor atual/não realizado/total em cards e
posições. Visão Geral: KPIs reais, tabela e barras de custo versus valor das
posições BRL cotadas. Demos continuam separadas (evolução patrimonial, alocação por
categoria, insights, caixa, metas, alertas, planejamento e análises avançadas).

Sem rede/token válido, CRUD local existente de Portfolio e registro/listagem de
BUY/SELL continuam disponíveis. Formulário não exige validação online de ticker.
Não há novas tabelas/colunas de mercado, Asset/PositionRepository, dividendos,
JCP, splits, impostos, câmbio, fundamentos, IA ou Alembic.

Testes: `tests/market/`, provider fake e httpx.MockTransport, inclusive falhas,
batch, precisão, persistência/reabertura e concorrência Qt. Suíte comum sem rede.
