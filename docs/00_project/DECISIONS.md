# Decisões do projeto

Resumo das decisões vigentes. Decisões com contexto e consequências próprias
devem receber ADR em `docs/02_architecture/decisions/`.

| Decisão | Estado/justificativa |
|---|---|
| Aplicação desktop em Python e PySide6 | Definida para a experiência e o contexto acadêmico. |
| SQLite com SQLAlchemy ou equivalente | Definido para persistência local prática. |
| Múltiplas carteiras | Cada estratégia possui identidade, histórico e resultados separados. |
| `Portfolio` persistido estruturalmente | Ao menos `id` e `name`; estado financeiro é reconstruído. |
| Incremento 01 | Somente criar/listar/selecionar Portfolio; ID inteiro gerado pelo SQLite, nome validado e duplicidade permitida. |
| Local da persistência SQL | `infrastructure/database/`; `persistence/` permanece vazio. |
| Contrato de carteiras | ABC PortfolioRepository em `domain/interfaces`, com `add` e `list_all`; sem repository genérico. |
| `Transaction` como ledger | Fonte principal de verdade financeira; ver [`ADR-001`](../02_architecture/decisions/ADR-001-transaction-ledger.md). |
| `Position` derivada | Sem tabela ou repositório próprios inicialmente. |
| `Asset` como objeto de valor | Identificado pelo símbolo; sem hierarquia por categoria. |
| Composição como relação interna principal | A carteira apresenta posições reconstruídas que contêm ativos. |
| Herança somente quando justificada | Não será usada artificialmente para demonstrar POO. |
| Polimorfismo em componentes intercambiáveis | Exemplo natural: provedores de mercado ou implementações de repositório. |
| Cálculos em `calculations` | Indicadores, projeções, risco e valuation ficam fora da UI. |
| Complementos não bloqueiam o núcleo | Planejamento, educação, IA e notificações externas têm prioridade inferior. |

Permanecem sem decisão: papel de `core` e uso efetivo de controllers/viewmodels. A localização do banco
para distribuição fora do checkout também permanece futura; no modo editável,
o caminho é `<raiz do checkout>/data/nexo.db`, independente de cwd.

## Incremento 02 — decisões financeiras

- Asset imutável com trim/uppercase e igualdade/hash pelo símbolo.
- Transaction imutável associada à carteira por ID; somente BUY/SELL.
- Replay integral no domínio, isolado por carteira/ativo.
- Compra incorpora taxas ao custo e recalcula média ponderada.
- Venda parcial remove quantidade vezes média; taxas reduzem receita líquida,
  sem alterar média remanescente. Resultado realizado é acumulado.
- Venda insuficiente lança InsufficientPositionError.
- Venda total consome custo restante exato e fixa quantidade/custo/média em zero.
  Recompra começa nova média e preserva resultado realizado anterior.
- positions retorna somente abertas; closed_positions preserva encerradas.
  Position não possui persistência ou repository.
- Decimal finito obrigatório, sem float/quantize; contexto local independente,
  ROUND_HALF_EVEN, mínimo 50 dígitos, ampliado pela magnitude/escala do histórico.
- Ordenação por data e ID crescente; IDs conhecidos precedem ausentes no mesmo
  timestamp. Ausentes e empates completos preservam ordem de entrada.
- Datas todas naive ou todas aware; aware ordenadas em UTC, mistura rejeitada.
- Sem caso de uso artificial, mudança de UI ou tabela nova.

Fórmulas e detalhes: [DOMAIN_MODEL.md](../02_architecture/DOMAIN_MODEL.md).

## Grande Incremento 03 — decisões vigentes da integração

O escopo foi ampliado por solicitação explícita: ledger e UI financeira no mesmo
incremento, antecipando o fluxo antes previsto para 04. Decisões de escopo 02
acima são históricas; as regras financeiras permanecem.

- TransactionModel separado, FK ativa em toda conexão e IDs AUTOINCREMENT.
- Decimal em TEXT via str/Decimal; datetime ISO TEXT preservando offset e naive.
- CREATE/READ somente; Position permanece derivada, sem tabela ou repository.
- RegisterTransaction reconstrói histórico completo antes de inserir, inclusive
  retroatividade. Mesmo timestamp: novo ID maior conserva ordem validada.
- Commit/rollback por operação; validação e escrita separadas, assumindo uma
  instância escritora local. Concorrência entre escritores não é suportada.
- Transaction.amounts centraliza política de taxas; UI só coleta/formata dados.
- Parser com ponto/vírgula decimal; agrupamento brasileiro apenas com vírgula
  decimal. Um ponto é decimal. Prefixos, sinais, expoentes e não finitos rejeitados.
- Formulário captura datetime naive; não atribui timezone silenciosamente.
- Dados locais reais em Carteiras/Movimentações/posições e métricas apropriadas
  da Visão Geral. Cotações, gráficos de mercado e complementos seguem demo.
- Após registro/troca, histórico, posições e resumo atualizam; falhas não expõem
  detalhes SQL nem conservam dados selecionados de outra carteira.


## Grande Incremento 04 — mercado e valuation

- brapi v2 com httpx, ABC MarketDataProvider e erros seguros independentes.
- Token opcional BRAPI_TOKEN (alias BRAPI_API_KEY), somente header Bearer.
- Lotes deduplicados entre carteiras; chunk configurável por plano; falhas parciais.
- Modelos de mercado imutáveis; JSON decimal lido com parse_float=Decimal.
- Valuation em calculations: valor aberto, não realizado, total e retorno aberto.
- Realizado vem exclusivamente do ledger, incluindo posições encerradas.
- Ledger BRL; moeda estrangeira preservada por linha, agregado indisponível sem FX.
- Dados ausentes não viram zero; carteira sem posições tem zero aberto legítimo.
- QRunnable/QThreadPool, sinais enfileirados e gerações contra respostas atrasadas.
- Refresh ao carregar/manual; sem cache do provider, somente fotografia da tela.
- Quotes e valuation não são persistidos. Offline preserva registro histórico.
- Renomeações/conversões de ticker não modificam automaticamente o ledger.

Detalhes e documentação oficial: [API_ARCHITECTURE.md](../02_architecture/API_ARCHITECTURE.md).
