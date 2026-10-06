# Status atual do projeto

## Fase atual

**Grande Incremento 04: mercado real, valuation das carteiras e dashboard.**
Em 06/10/2026, preservando o fluxo financeiro do incremento 03.

## Funcionalidades reais

- Portfolio persistido: criar/listar/selecionar por ID, nomes iguais permitidos.
- Ledger SQLite BUY/SELL, validação do replay antes do INSERT, FK/rollback,
  Decimal TEXT e datas ISO preservadas. Formulário histórico funciona offline.
- Histórico local com filtros; Position derivada, média, custo e realizado.
- MarketDataProvider independente, BrapiMarketDataProvider/httpx isolado.
- brapi v2: quotes em lote, catálogo/search e histórico diário real.
- Token opcional externo, app inicia sem token; símbolos públicos disponíveis
  conforme API. Falhas de acesso/limite/conexão traduzidas sem expor credenciais.
- Decimal direto do literal JSON; nenhum cálculo financeiro em float.
- LoadPortfolioValuation compartilha batch deduplicado entre carteiras.
- calculations/valuation: custo investido aberto, valor atual, não realizado,
  realizado incluindo encerradas, total e retorno sobre custo aberto.
- BRL agregado somente completo; moedas diferentes não convertidas/somadas.
- Ativos: busca real, seleção, cotação/moeda/variação, fonte/referência/consulta,
  período 1M/3M/1A e gráfico real de fechamento (pode ser ajustado pela API).
- Carteiras: cards reais e posições com preço/valor/não realizado/retorno;
  “Atualizar” renova dados locais e valuation.
- Overview: KPIs reais, posições e barras reais custo versus valor BRL cotado.
- TaskRunner Qt fora da thread GUI, callbacks enfileirados e gerações para
  descartar respostas antigas após trocar carteira/ativo/busca/período.
- Atualização inicial/de contexto e manual, sem polling. Sem cache do provider;
  fotografia visual reutilizada no mesmo contexto, com timestamps identificados.
- Sem tabelas/colunas/repositories de Quote, Asset, Position ou valuation.

## Offline e estados incompletos

Ledger, média, custo, realizado e transações continuam disponíveis. Mercado
indisponível usa “—”, nunca zero/demo. Quotes parciais conservam linhas válidas,
mas agregado dependente de todas fica indisponível. Moeda estrangeira exibe
preço/valor na moeda própria, sem P/L contra BRL. Sem posições abertas, valor
aberto é zero legítimo e resultado realizado encerrado é preservado.

## Ainda demonstrativo ou futuro

Evolução patrimonial histórica, alocação por categoria, benchmarks, insights,
fluxo de caixa, metas, alertas, planejamento, projeções e análises complementares
seguem demo com badges. Não há caixa/aportes/retiradas, dividendos/JCP, impostos,
splits, conversão de ticker/câmbio, fundamentos detalhados, IA ou Alembic.
Mercado das posições abertas não é patrimônio total. Comparação e edição/exclusão
de Portfolio/Transaction continuam pendentes.

## Validação em 06/10/2026

- Baseline 245 casos aprovada; nenhuma remoção/alteração de testes antigos no 04.
- 77 novos casos: adapter MockTransport, fake substituível, batch/parciais,
  moeda, precisão, SQLite/configuração/reabertura e Qt/concorrência.
- Suíte completa: 322 coletados/aprovados, zero falhas.
- Ruff, mypy src (56 arquivos), compileall e git diff --check aprovados.
- Imports auditados: Domain/Application/Calculations sem HTTP/ORM/Qt;
  UI sem SQL/HTTP/infra. main.py compõe as dependências concretas.
- Smoke real online sem token pelo adapter: 2 quotes PETR4/VALE3, 9 resultados
  PETR e 21 pontos PETR4/1mo. Preços observados não são hardcoded ou persistidos.
- Timeout/conexão/autenticação/limite/JSON inválido cobertos sem internet.
- Roteiro UI com tema real/banco temporário: Mercado teste, BUY10 PETR4@30,
  quote HTTP controlada40, quantidade10, média30, custo300, valor400, não
  realizado100; reabertura com quote45 =>450, ledger permanece uma operação.
- Cenário custo528/quantidade15/realizado33 + quote40 =>600/72/105 validado.
- Capturas Overview/Ativos revisadas; contraste de seleção/botões e largura
  dos KPIs ajustados. Entry point iniciou/encerrou em processo sem token.
- Sem commit/push ou mudanças de schema neste incremento; edições 03 preservadas.

## Limites e próximos passos

1. Comparação de carteiras com métricas, moedas e disponibilidade documentadas.
2. Políticas de edição/exclusão e evolução histórica/benchmarks reais.
3. Revisão prolongada/DPI e teste de plano autenticado real.
4. Proposta aprovada, calendário e confirmação acadêmica de A-008.

Validação e INSERT separados assumem uma instância escritora local; escritores
concorrentes não são suportados. A API pode atrasar/limitar dados conforme plano.
Workers pendentes são limpos ao fechar; os ativos terminam sob timeout antes de
fechar client/engine, sem cancelamento HTTP instantâneo. Papel de core e
localização do banco para distribuição continuam futuros.

Detalhes: [API_ARCHITECTURE.md](../02_architecture/API_ARCHITECTURE.md) e
[TESTING.md](../04_development/TESTING.md).
