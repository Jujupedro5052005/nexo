# Estratégia de testes

## Suíte atual — Grande Incremento 04

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
