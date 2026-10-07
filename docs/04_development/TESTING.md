# Estratégia de testes

## Dashboard visual — 07/10/2026

Suíte completa: **574 aprovados**, zero falhas, em 297,73 s; 566 casos anteriores
preservados e oito novos em `tests/ui/test_dashboard_visuals.py`. Cobertura:
donut com pesos originais, soma de “Outros” e tabela completa, ativo único,
carteira vazia/incompleta, cards alinhados/empilhados e reset das cores/estado.
Ruff, mypy src (90 arquivos), compileall e git diff --check aprovados.
Nenhuma chamada externa na suíte.

Entry point executado com `.venv\Scripts\python.exe -m nexo.main --demo`
em Windows nativo e encerrado normalmente; modo normal validado em banco
isolado. Capturas revisadas em `tmp/dashboard_visuals/`: donut e tabela,
dashboard, par Evolução/Insights desktop e empilhamento em janela estreita.
Capturas detalhadas reutilizam cotações reais previamente capturadas, mantendo
valores/fontes/horários; não adicionam fixtures ao modo demo do produto.

## Validação do ambiente demo — 07/10/2026

Suíte completa: **566 aprovados**, zero falhas, em 271,66 s; baseline de 550
preservada e 16 novos casos. Ruff aprovado; mypy src aprovado em 89 arquivos;
compileall e git diff --check aprovados. Nenhuma chamada externa na suíte.

## Suíte atual — Incremento 05.1

Baseline 432 preservada. 35 casos novos em tests/brapi_config; 467 coletados.
Suíte completa final: 467 aprovados, zero falhas, em 179,86s.

Cobertura: .env real temporário/default raiz/cwd/BOM, precedência por nome/origem,
whitespace/alias, ausência/legado, capability pública, status sem segredo, ITSA3
sem token (quote/histórico/fundamentos/proventos), busca antes da restrição, Bearer
fake em header e fora da URL, 401/403/429/timeout/conexão, teste novo sem cache,
UI Configurações/Ativos/navegação, worker/heartbeat e erro inesperado sanitizado.

Teste Windows externo à suíte: PETR4 público e conexão real funcionaram; ITSA3
sem chave deu configuração necessária, não AssetNotFound. Configuração externa
não tinha chave real; acesso ITSA3 autenticado foi validado apenas por transporte
controlado. Nenhuma chave real foi impressa, salva ou exigida pelos testes comuns.

Ruff check ., mypy src (72 arquivos), compileall e git diff --check aprovados.
Capturas Windows/tema real revisadas: explicação ITSA3, navegação e Configurações.

Detalhes: [BRAPI_CONFIGURATION.md](../02_architecture/BRAPI_CONFIGURATION.md).

## Evidência histórica — Grande Incremento 05

Baseline confirmada antes das alterações: 322 coletados/aprovados. Testes anteriores
não foram removidos ou alterados. 110 novos casos em tests/analytics; 432 coletados.
Suíte completa final: 432 aprovados, zero falhas, em 182,86s.

- Fórmulas: Graham/Bazin/margem, indicadores/missing/denominadores/negativos/FX,
  política DIVIDENDO/JCP/data/verified, volatilidade amostral/252, drawdown e HHI.
- Provider: MockTransport com contratos v2 reais, Decimal nullable/fallback,
  módulo parcial, moeda, envelope/ticker alterado, campos inválidos e proventos.
- Cache: relógio injetado, TTL, chaves por período/janela, limites, erros não
  cacheados, batch/deduplicação, coalescência e invalidação de consultas em voo.
- Application/SQLite: IDs com nomes iguais, custo/realizado/não realizado/total,
  vazio, offline, dados parciais/FX, schema inalterado e atualização explícita.
- Pipeline integrado: SQLite → posições → adapter HTTP controlado → cache →
  análise/valuation/comparação, preservando ledger e sem tabelas derivadas.
- Qt: fundamentos/margens reais, mudança de yield/contexto limpa a tela;
  heartbeat antes de liberar Event e resposta atrasada de ativo/comparação
  rejeitada. Atualização global e registro de transação invalidam análise relevante.

Suíte normal não acessa internet, .env ou banco do usuário. Mocks do provider/API
são exclusivos de testes; produção é composta com BrapiMarketDataProvider.

Roteiro externo à suíte em 06/10/2026:

1. PETR4 público pelo adapter/cache/AnalyzeAsset real, sem carregar credenciais:
   quote BRL, EPS/VPA/referência contábil, dez indicadores, Graham/Bazin com yield
   explícito de 6%, margem e 21 fechamentos de 1mo, sem avisos de erro.
   DIVIDENDO por padrão, JCP excluído; retorno de 10 eventos elegíveis no snapshot.
   Preços observados são temporais, não hardcoded nem assertions da suíte comum.
2. SQLite temporário + tema real: duas carteiras com mesmo nome e IDs 1/2,
   BUY10 PETR4@30 e BUY20 VALE3@20; provider controlado de contrato substituível
   retorna 80/40. Custos 300/400 e valores 800/800; maior/top3/HHI 1 em cada uma.
   Fundamentos controlados 4/20 e DIV6 => Graham≈42,43, Bazin100 (yield6%), margem20%.
3. Retirada controlada de VALE3: custo400 preservado, valor/concentração “—” e
   ticker explicitamente indicado. Troca de seleção limpa comparação/gráfico.
   Capturas revisadas após assentamento do layout: tabs/tema/tabelas legíveis;
   texto extenso de origem/fórmula preservado em tooltip, sem comparação por pixel.
4. Entry point iniciou/encerrou com SQLite temporário e configuração sem token.
   Encerramento espera todos os workers antes de fechar client/engine.

Ruff check ., mypy src (69 arquivos), compileall e git diff --check aprovados;
imports auditados por AST: nenhuma violação HTTP/ORM/Qt entre as camadas.
DPI/uso interativo prolongado e plano autenticado real permanecem pendentes.

## Evidência histórica — Grande Incremento 04

Baseline confirmada: 245 aprovados, preservados sem alterar/remover testes antigos.
77 casos novos em `tests/market/`: adapter, valuation, contratos/Application,
SQLite/reabertura/configuração e UI/concorrência. Total: 322 casos.

- Adapter: httpx.MockTransport, v2/envelopes, Decimal literal/string, lote/chunks,
  autenticação/header seguro, inexistente, timeout/conexão, HTTP/JSON inválido,
  timestamps, histórico diário/renomeação e catálogo.
- Cálculos: ganho/prejuízo, 15 × 40 = 600, custo 528, não realizado 72, realizado
  33 e total 105; carteira vazia/encerrada, ausências/parciais, FX não fictício,
  precisão global independente e três ativos distintos fora da ordem de resposta.
- Contrato: FakeProvider substitui brapi sem HTTP. Carteiras compartilham batch,
  vazias não consultam provider, falha preserva métricas locais.
- SQLite + adapter real com HTTP controlado: ledger reaberto, nova quote modifica
  somente valuation, schema continua portfolios + transactions.
- Qt: KPIs/tabelas/cards/barras reais, refresh, rede falha sem bloquear BUY,
  thread worker diferente da GUI e callback na GUI, respostas atrasadas descartadas
  ao trocar carteira/ativo, busca/seleção/período e série sem fallback demo.
- Concorrência: Event controla chamada lenta; heartbeat GUI é observado antes de
  liberar o worker. Asserções por estado/sinais; sem timing presumido ou pixels.

Suíte comum não acessa internet/banco do usuário. Smoke online separado via
BrapiMarketDataProvider sem token: 2 quotes públicas, 9 resultados PETR e 21
pontos PETR4/1mo em 06/10/2026. Valores temporais não são assertions normais.

Roteiro representativo fora da suíte, SQLite temporário e tema real: carteira
Mercado teste, BUY10 PETR4 @30 pela UI, quote HTTP controlada 40 => quantidade10,
média30, custo300, valor400 e não realizado100; após reabertura, quote45 =>450,
ledger com uma operação intacta. Capturas Ativos/Overview conferidas, sem assert
por pixel. Entry point iniciou/encerrou em processo separado sem token.

Offline/timeout controlados e falhas de provider não impedem ledger local.
DPI/uso interativo prolongado e plano autenticado real ainda não validados.

## Evidência histórica — Grande Incremento 03

245 casos coletados/aprovados, zero falhas; 86 novos testes.
Baseline de 159 testes confirmada antes das alterações. A expectativa de schema
portfolios-only foi legitimamente atualizada para portfolios + transactions;
as demais verificações antigas foram preservadas.

Novos testes cobrem persistência BUY/SELL, IDs, FK ativa, Decimal/datetime/Enum/
Asset round-trip, isolamento, ordenação aware, rollback, reabertura e banco antigo.
Application cobre saldo, retroatividade, mesmo timestamp, erro de storage,
listagem, reconstrução e resumos. Parser cobre gramática e limites. pytest-qt
cobre seleção, vazio, BUY/SELL, erros, filtros, atualizações e outra janela após
reabrir SQLite. O cenário PETR4 confere 15 unidades, média 35.2, custo 528,
realizado 33 e rejeição de venda 16 sem INSERT.

Testes usam SQLite temporário ou repository em memória; não acessam data/nexo.db
nem internet. Captura representativa usa o tema real; assertions são por estado
e conteúdo, sem comparação por pixel. Roteiro interativo prolongado/DPI ainda
é pendente. Estratégia para os demais recursos permanece abaixo.

```text
tests/
├── unit/
│   ├── domain/
│   ├── application/
│   └── calculations/
├── integration/
│   ├── database/
│   ├── market_data/
│   └── notifications/
├── ui/
├── market/  # suíte vertical do incremento 04
├── analytics/  # suíte vertical do incremento 05
└── fixtures/
```

## Unitários

Domain e Calculations devem ter cobertura forte de invariantes, `Decimal`,
compras, vendas, preço médio, reconstrução de posições, isolamento entre
carteiras e métricas. Application é testada com repositórios e providers falsos
para verificar coordenação e falhas sem banco ou rede.

## Integração

Banco: schema, mapeamento ORM/domínio, vínculo por `portfolio_id`, rollback,
persistência após reabertura e preservação de datas/decimais.

Dados de mercado e notificações: contratos, conversão de respostas, timeouts e
erros. Testes reais de serviços externos devem ser separados da suíte comum e
nunca exigir credenciais versionadas.

## UI

Quando viável, usar pytest-qt para seleção de carteira, submissão de formulários,
mensagens, estados vazios e atualização de telas com casos de uso falsos. Manter
também roteiro manual dos fluxos críticos no Windows.

## Execução

```powershell
pytest
pytest --cov=src/nexo
```

Estrutura vazia ou teste planejado não conta como evidência de requisito
atendido. A suíte deve permanecer determinística e independente da internet por
padrão.

Inicialização do entry point nexo.main validada em processo separado com banco
temporário, encerramento automático e fechamento explícito da conexão de inspeção.
Ruff, mypy src, compileall e git diff --check aprovados em 06/10/2026.

## Multi-provider — 05.2 (07/10/2026)

`tests/providers/` valida routing/cache/TTL/capability negativa/budgets/contador
persistente/coalescing, parsing bolsai/Yahoo, cadastro/DFP/ITR CVM, bridge exato,
metadata/source, snapshots/parciais, latência/frescor, provider health e UI.
Todos os 467 casos existentes são preservados; quatro expectativas de default
passam de batch5 para batch1 e o teste de batch3 explicita essa capacidade.
Nenhum teste foi removido. TTLs reais são verificados por relógios injetados.

A fixture autouse comum bloqueia HTTPTransport, requests, curl_cffi e sockets;
falha no teardown mesmo se o adapter capturar a tentativa. Dados são fixtures,
MockTransport, DataFrame/factory fake e CSV/ZIP oficiais pequenos.

Economia em Qt/fakes: 3 ciclos Ativos/Análises/Overview/Carteiras, reconsulta do
ativo e recálculo da análise. Operações efetivas simuladas: brapi3 (quote/search/
history), bolsai1 (fundamentals), Yahoo1 (dividends), CVM0. Internet real0.
24 hits brapi medidos; concorrência de três consultas idênticas também coberta.

Smoke online separado: `python scripts/smoke_providers.py`, executado uma vez.
Consumiu brapi2, bolsai0 (chave ausente), Yahoo1 operação de ticker, CVM0 downloads.
B3SA3: preço 22,68 BRL, variação -0,62/-2,66%, máxima23,93, mínima22,44,
volume80.683.500, market cap113.202.887.016 BRL, fonte brapi, latência240ms,
timestamp2026-10-06T21:31:30Z e atraso estimado do plano~30min.
Timestamp da consulta2026-10-07T11:09:41Z; idade do dado exibida separadamente,
sem chamar a resposta rápida de tempo real.
PETR4 1mo via brapi validado. ITSA4 1y via Yahoo teve250 fechamentos e7 proventos,
normalizados como CASH_DISTRIBUTION por data-ex com pagamentoNone.

Fundamentos/bridge bolsai e cadastro/DFP/ITR CVM **não validados online** nesta
sessão por falta de BOLSAI_API_KEY e bridge válido de ITSA4; testes com fixtures
não substituem esse aceite. Smoke tem CVM budget0 e jamais baixa datasets.
A captura real de B3SA3 foi revisada em Qt nativo Windows; render offscreen dessa
máquina não dispõe do mesmo acesso a fontes, portanto não é evidência visual.

Artefatos locais sanitizados (ignorados no Git): `tmp/providers_smoke.json`,
`tmp/B3SA3_snapshot.png` e `tmp/provider_economy.xml`. O último registra as ações,
requests simulados e24 cache hits. `python scripts/preview_snapshot.py` recria a
captura a partir do relatório, sem rede adicional.

A baseline recebida no workspace executou466 aprovados/1 falha antes das mudanças:
.env.example estava preenchido; campos de exemplo foram esvaziados e o .env local
preservado. A suíte posterior voltou a passar com os467 casos preservados.

Atualização explícita de demonstrações invalida resultados CVM normalizados,
reutiliza datasets válidos e permite preencher DFP que ficou ausente pelo budget
inicial; cadastro/ITR não são baixados novamente. Cobertura também inclui
remaining=0/reset UTC, fallback com primário vazio, ROE parcial, health Yahoo429,
e precisão de percentuais/escala monetária sob contexto Decimal externo restrito.

Inicialização nativa Windows em banco temporário: exit0, requests brapi0,
bolsai0, Yahoo0 e CVM0. Nenhum dataset real baixado para completar fixtures.

Resultado final em07/10/2026: **550 testes aprovados, zero falhas,235,93s**.
Baseline467 preservada e83 novos casos. Ruff check ., mypy src (88 arquivos),
compileall src/tests/bootstrap_project.py e git diff --check aprovados.
Último teste acrescentado comprova que refresh sem carteiras não concede bypass
de budget a uma consulta automática posterior. Código não foi alterado após
esta rodada completa; documentação recebeu somente o registro do resultado.
# Dataset de demonstração acadêmica

Testes adicionais em `tests/integration/test_demo_dataset.py` e
`tests/ui/test_demo_presentation.py`: schema existente, três carteiras/93 operações,
21 posições, histórico de 30 meses, vendas válidas/rejeição de oversell, IDs e
Decimais, reset idempotente, proteção do banco normal/hardlink, falha atômica,
primeira abertura/reabertura, CLI e caminhos normal/demo. UI cobre dez páginas,
gráficos de três carteiras, comparação e dois ativos com doubles explicitamente
restritos aos testes. A barreira de rede da suíte continua ativa.

Seed offline: `python scripts/create_demo_dataset.py`.
Verificação nativa online opcional: `python scripts/check_demo_presentation.py --online`.
Limites e evidências em [DEMO_PRESENTATION.md](DEMO_PRESENTATION.md).
