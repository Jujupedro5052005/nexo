# Status atual do projeto

## Busca manual de ativos / Enter — 07/10/2026

Corrigido bloqueio por budget local ao enviar pesquisa pelo Enter ou Buscar.
SearchAssets recebe explicit=True apenas no worker da busca manual. Seleção
do resultado propaga o escopo manual para cotação, histórico e análise sem
invalidar caches válidos; mudança de período também é consulta manual.
Atualizar ativo continua invalidando uma vez. Chamadas Application automáticas
mantêm explicit=False e quotas/limites remotos permanecem respeitados.

Regressão Qt: PETR4 + Enter → resultado → seleção → Atualizar ativo, com budget
zero, bolsai ausente ou indisponível. Dados pela brapi, nenhuma chamada bolsai,
consulta automática posterior bloqueada. Verificações sem rede.

## Diagnóstico de Atualizar mercado — 07/10/2026

Teste externo à suíte com composição real e cópia SQLite do demo: clique no
botão global propagou explicit=True ao worker e retornou valuation completo
para as três carteiras via brapi. Consulta isolada PETR4 também respondeu;
contador local acima do budget automático, sem apagar/resetar contadores.
Banco normal e demo originais preservados. Falha relatada não reproduzida.

Corrigido feedback que permanecia em Consultando mercado quando a consulta
terminava sem carteira selecionada. Agora orienta seleção, mantendo os valores
nos cards de Carteiras. Erros tipados seguros do worker aparecem na mensagem;
detalhes de erros internos continuam ocultos. 321 testes direcionados passaram
sem internet; Ruff, mypy src, compileall e git diff --check aprovados.

## Atualizar ativo / fallback de fundamentos — 07/10/2026

Atualizar ativo agora propaga o escopo manual para os workers de cotação,
histórico e análise, invalidando o cache compartilhado uma única vez.
Fundamentos: brapi → bolsai → CVM; erros ou ausência de campos financeiros
permitem fallback, mantendo fonte e cálculos existentes. Cache brapi de
fundamentos: 12 h. Cotação continua brapi → bolsai.

318 testes de providers/market/analytics/brapi_config aprovados sem internet;
cobertura inclui botão Qt sem chave bolsai, budget esgotado, prioridade brapi
sem consultar bolsai e fallback bolsai após erro ou resposta vazia da brapi.
Ruff, mypy src (90 arquivos), compileall e git diff --check aprovados.
Disponibilidade online dos módulos continua condicionada ao plano do provider.

## Diagnóstico PETR4 / integração — 07/10/2026

- brapi continua prioritária para cotação. Falha automática observada ocorreu
  com contador local271 acima do soft budget100; atualização explícita de
  PETR4 retornou cotação brapi. Sem apagar contadores ou alterar budgets/plano.
- Com a chave bolsai configurada, cotação e fundamentos PETR4 retornaram
  corretamente em consultas pontuais; indisponibilidade anterior não reproduzida.
- Se ambas as fontes falham, routing conserva categoria/diagnóstico da brapi e
  informa o erro do fallback. bolsai diferencia HTTP, autenticação, plano,
  limite e timeout; corpos/segredos não aparecem na mensagem.
- Cópia da chave brapi removida de `.env.example`, mantendo a chave do `.env`.
  Sete regressões adicionadas para prioridade PETR4, budget/fallback,
  atualização explícita, status HTTP e timeout; testes sem internet.

## Revisão visual do dashboard — 07/10/2026

- Concentração agora em donut com os pesos existentes, tabela completa,
  maior posição, top 3/tickers e HHI; agrupamento visual “Outros” acima de oito
  ativos, sem alteração de regras financeiras.
- KPIs de mercado em destaque, microdescrições e cores de resultado; fundo
  dark nos gráficos. Evolução/Insights compartilham um par responsivo 3:1,
  alinhado no desktop e empilhado na janela estreita.
- Mudanças exclusivamente na UI; schema, dataset, providers e cálculos preservados.
- Entry point `--demo` iniciado/encerrado em Windows; modo normal validado com
  banco isolado. Capturas em `tmp/dashboard_visuals/` (ignoradas); revisão de
  gráficos/layout reutilizou cotações reais capturadas para poupar APIs.
- Validação: **574 testes aprovados**, zero falhas (297,73 s), preservando os
  566 anteriores; oito novos testes de donut/pesos/agrupamento, estados e layout.
  Ruff, mypy src (90 arquivos), compileall e git diff --check aprovados.

## Ambiente de demonstração acadêmica — 07/10/2026

- `python scripts/create_demo_dataset.py`: seed offline, idempotente e atômico
  exclusivo de `data/nexo_demo.db`, usando casos de uso/repositories existentes.
- `python -m nexo.main --demo`: cria na primeira abertura, preserva nas demais,
  seleciona Longo Prazo e identifica dados fictícios no título/status da janela.
- Três carteiras, 93 movimentações, 21 posições, 16 tickers e 30 meses
  (abril/2024–setembro/2026), compras recorrentes e nove vendas parciais.
- Interface nativa: dez páginas, valuation completo de todas as carteiras,
  gráficos de custo/valor/concentração e comparação com 21 posições conferidos.
- PETR4/B3SA3: quote/OHLCV, 21 pontos históricos e quatro proventos cada;
  fundamentos/cadastro indisponíveis sem chave bolsai. Nenhum fallback fictício.
- Verificação e complementação: brapi20/Yahoo2/bolsai0/CVM0. Capturas/JSON
  ignorados em `tmp/demo_presentation/`; banco normal preservado por comparação
  de hash. Complementação visual reutilizou cotações reais capturadas.
- Evolução patrimonial, caixa e funcionalidades demonstrativas anteriores
  conservam suas limitações; dataset não as promove a cálculos funcionais.
- Instruções, valores observados, cobertura e roteiro:
  [DEMO_PRESENTATION.md](../04_development/DEMO_PRESENTATION.md).
- Validação: suíte completa **566 aprovados**, zero falhas (271,66 s), incluindo
  os 550 anteriores e 16 novos; Ruff, mypy src (89 arquivos), compileall e
  git diff --check aprovados. Suíte e seed sem chamadas externas.

## Fase atual

**Incremento 05.2: multi-provider, fontes oficiais, quotas e snapshot avançado.**
Em 07/10/2026, preservando as entregas 01–05.1, domínio, ledger e schema.

## Entrega 05.2

- Routing por capability: brapi mercado; bolsai fundamentos/metadados/EOD;
  Yahoo histórico longo/proventos/actions; CVM cadastro/DFP/ITR oficiais.
- Contratos separados, composição em main.py, HTTP/datasets/yfinance somente
  Infrastructure; sem provider universal ou alteração do modelo financeiro.
- Snapshot avançado em Ativos: preço/variação/OHLCV/market cap, origem, horários,
  latência, atraso estimado e idade do dado; JSON normalizado recolhível.
- Cache compartilhado por fonte/capability com TTLs fechados; coalescing também
  cobre decisão de fallback. Sem polling ou auto-refresh por navegação.
- Usage JSON persistente sem segredo, budgets 100/40/50/2, remaining bolsai,
  capability negativa 403 por 12 h, health por operação e diagnóstico local.
- Bridge ticker/CNPJ/CVM em cache de sete dias; cadastro completo e ZIP anual
  com TTL24h. Consolidados preferidos, individual fallback, versão/período
  selecionados sem soma. Contas oficiais/raw/cross-check técnico conservador.
- Bazin consome DividendDataProvider. Yahoo mantém CASH_DISTRIBUTION, pagamento
  None e janela por data-ex, com limitações explícitas; splits não alteram ledger.
- yfinance adicionado; .env.example contém somente campos vazios. .env preservado.
- Smoke separado validou B3SA3 completo e 1mo brapi; 1y Yahoo (250 pontos) e
  ITSA4 proventos (7 eventos). Consumo: brapi2, bolsai0, Yahoo1 operação, CVM0.
- bolsai sem chave na sessão: fundamentos e bridge/cadastro oficial ITSA4 ainda
  não validados online. Fixtures não são apresentadas como autenticação real.
- Captura nativa Windows do snapshot real revisada; navegação por quatro telas
  e economia validadas em Qt/fakes, com 24 hits brapi e cinco operações simuladas.

Políticas e limites atuais: [DATA_PROVIDERS.md](../02_architecture/DATA_PROVIDERS.md).
As seções abaixo registram a baseline histórica e não substituem o routing/TTLs 05.2.

## Baseline 01–05.1 preservada (histórico)

- Portfolio com ID/nome persistido; criação/listagem/seleção, nomes iguais permitidos.
- Ledger SQLite BUY/SELL, replay validado antes do INSERT, FK/rollback, Decimal TEXT
  e datetime ISO; posições/média/custo/realizado reconstruídos, registro offline.
- Mercado brapi v2: busca real, quotes em lote deduplicado, histórico diário 1M/3M/1A.
- FundamentalDataProvider separado; mesmo adapter/httpx.Client; estatísticas atuais,
  dados financeiros atuais e proventos por janela, com Decimal/None/origem/consulta.
- Dez indicadores reais: LPA, VPA, P/L, P/VP, DY da janela, ROE, ROA, margem líquida,
  margem EBITDA e dívida líquida/EBITDA; fórmula/origem e indisponibilidade visíveis.
- Graham sqrt(22,5×LPA×VPA) positivo; Bazin com yield requerido explícito em %, sem
  default; diferença/margem neutras, sem recomendação automática de compra/venda.
- Proventos por ação da janela de pagamentos: DIVIDENDO por padrão; JCP bruto
  opcional, sem imposto; futuros/verified=False excluídos. Sem crédito no ledger.
- Risco do histórico do ativo: volatilidade amostral diária/anualizada (252 pregões)
  e drawdown máximo. Sem tratá-los como performance histórica da carteira.
- Ativos e Análises compartilham painel real; Análises possui comparação de 2+ IDs,
  com custo/valor/realizado/não realizado/total/retorno aberto e posições.
- Pesos reais por valor aberto, maior/top3/HHI sem score arbitrário, somente quando
  valuation BRL completo/positivo; concentração também em Carteiras/Visão Geral.
- Overview mantém KPIs reais, posições e custo/valor; alocação demo por categoria
  removida e substituída por concentração real por ativo.
- Cache TTL compartilhado em memória: quotes30s, histórico300s, fundamentos/
  proventos300s, limite256; coalescência, deduplicação e refresh explícito versionado.
- TaskRunner Qt fora da GUI, sinais enfileirados e gerações por contexto/premissa.
  Atualização global recarrega análise visível; transação invalida comparação.
- Sem schema, tabelas, snapshots ou repositories derivados adicionais; HTTP só
  Infrastructure, cálculos em calculations, main.py compõe os contratos/concretos.

## Configuração e UX — Incremento 05.1

- Auditoria confirmou .env automático na raiz via python-dotenv já existente;
  main.py injeta MarketSettings.from_environment. Sem dependência adicional.
- Precedência: ambiente sobre o mesmo nome no arquivo; depois TOKEN não vazio
  sobre API_KEY não vazio, ambos normalizados. Leitura UTF-8/BOM aceita.
- Status/capabilities sem segredo, lista pública centralizada e autenticação
  desconhecida distinta de chave configurada. Configurações agora funcional.
- Testar conexão consulta PETR4 fresco pelo mesmo adapter/client, fora da GUI.
  Sucesso público não prova acesso a ITSA3; erros 401/403/429/conexão distintos.
- ITSA3 sem chave explica permissão para detalhes, sem tratá-lo como inexistente;
  Configurar integração abre Configurações. Sem editor de .env ou segredo na UI/SQL.
- .env.example e README orientam arquivo local e alternativa PowerShell;
  MARKET_API_* são legados e não configuram a brapi. .env do usuário preservado.

## Offline, incompletos e moedas

Ledger/média/custo/realizado continuam locais. None é mostrado como “—” com motivo;
não vira zero/demo. Falha de módulo de fundamentos conserva os campos disponíveis.
Quotes válidas mantêm linhas, mas ausência/FX de qualquer posição invalida agregado
BRL e todos os pesos; não se renormaliza a parte disponível. Preço/valor estrangeiro
permanece na moeda própria; nenhum múltiplo, margem ou resultado contra BRL inventado.
Carteira vazia/encerrada pode ter zero aberto legítimo, preservando realizado; não
possui percentual de retorno ou concentração sem denominador positivo.

## Performance e demos remanescentes

Retorno não realizado / custo aberto é uma fotografia, não rentabilidade histórica.
Realizado + não realizado é resultado monetário. TWR deliberadamente indisponível:
faltam caixa, fluxos externos explícitos e avaliações completas nos limites de fluxo.
Compras/vendas não são aportes/retiradas para TWR ou XIRR. XIRR/MWR, Sharpe e benchmark
não calculados sem suas bases. Desenho futuro TWR documentado, não implementado.

Evolução patrimonial histórica, benchmarks, insights, caixa, metas, alertas,
planejamento e relatórios continuam demonstrativos com identificação por seção.
Sem crédito de proventos no ledger, impostos, splits, FX, conversão de ticker,
edição/exclusão, IA ou Alembic. Valor aberto não representa patrimônio incluindo caixa.

## Validação em 06/10/2026 — 05.1

- Baseline 432 preservada; 35 novos casos, 467 coletados.
- Suíte final: 467 aprovados, zero falhas (179,86s).
- Ruff check ., mypy src (72 arquivos), compileall e git diff --check aprovados.
- Capturas com tema real revisadas para ITSA3/Configurações e navegação.
- Arquivo/cwd/BOM/precedência, sandbox/Bearer, ITSA3, estados HTTP, status seguro,
  navegação e worker/heartbeat cobertos sem rede nos testes comuns.
- Teste real público Windows: PETR4 disponível e conexão funcionando;
  ITSA3 sem token classificado como configuração necessária, não inexistente.
- Nenhuma chave real disponível na configuração externa da sessão; ITSA3 com
  token validado apenas com MockTransport. Sucesso autenticado real não afirmado.
- Sem schema/dependência nova, alteração financeira, commit/push ou edição do .env.
- Baseline 05 verificada anteriormente: 432 aprovados; smoke PETR4 de fundamentos/
  valuation e comparação em SQLite temporário continuam documentados em TESTING.

## Limites e próximo incremento

Recomendado (não implementado): caixa e fluxos externos explícitos para preparar
patrimônio histórico/TWR, com políticas próprias de taxas/proventos/eventos/moedas.
Plano autenticado real, DPI/uso prolongado, acessibilidade e cancelamento HTTP
instantâneo continuam pendentes; workers ativos terminam sob timeout antes de
fechar client/engine. Cache não garante dados em tempo real; timestamps preservados.
Revisão de core/localização do banco para distribuição ainda futura.

Uma instância escritora local continua pressuposta; validação e INSERT separados
não garantem concorrência entre escritores. Proposta aprovada, calendário e
confirmação acadêmica de A-008 permanecem pendentes.

Detalhes: [BRAPI_CONFIGURATION.md](../02_architecture/BRAPI_CONFIGURATION.md),
[ANALYTICS.md](../02_architecture/ANALYTICS.md),
[API_ARCHITECTURE.md](../02_architecture/API_ARCHITECTURE.md) e
[TESTING.md](../04_development/TESTING.md).

## Validação final 05.2 — 07/10/2026

- pytest: **550 aprovados**, zero falhas (235,93 s); baseline467 +83 novos casos.
- Ruff check .: aprovado.
- mypy src: aprovado,88 arquivos-fonte.
- compileall src/tests/bootstrap_project.py: aprovado.
- git diff --check: aprovado.
- Zero chamadas externas na suíte; smoke separado brapi2/bolsai0/Yahoo1/CVM0.
- Produto implementado e verificado com fixtures; aceite online de fundamentos/
  bridge bolsai e cadastro/DFP/ITR CVM pendente por ausência de chave/bridge.
