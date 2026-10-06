# Status atual do projeto

## Fase atual

**Incremento funcional 02 concluído: domínio financeiro e reconstrução
determinística em memória. Carteiras persistentes do incremento 01 preservadas;
fluxo financeiro da interface ainda demonstrativo.**

## Implementado

- pacote editável com runtime declarado a partir de `requirements.txt`;
- entry point `python -m nexo.main`;
- janela PySide6, tema dark, ícones e navegação entre dez páginas;
- `Portfolio` imutável com `id: int | None`, nome obrigatório e trim;
- igualdade de entidades persistidas pelo ID, sem unicidade de nome;
- abstração `PortfolioRepository` e erro independente de detalhes SQL;
- casos de uso `CreatePortfolio` e `ListPortfolios`;
- `PortfolioModel` distinto da entidade de domínio;
- implementação SQLAlchemy em `infrastructure/database/`;
- schema real somente `portfolios(id INTEGER PRIMARY KEY, name TEXT NOT NULL)`;
- sessões por operação, commit antes do retorno e rollback em falha;
- banco `data/nexo.db` resolvido pelo checkout, sem depender de cwd;
- composição de banco, repositório, casos de uso e janela em `main.py`;
- página Carteiras real, com estado vazio, atualização e seleção por ID;
- `PortfolioDialog` funcional, somente com campo nome e feedback de erro;
- `MainWindow.selected_portfolio_id`, sem persistir seleção entre execuções;
- carteiras vazias sem patrimônio/rentabilidade fictícios;
- falhas de leitura/gravação sem expor detalhes técnicos na UI;
- correção dos dois acessos potencialmente `None` apontados pelo mypy no overview.

## Ainda demonstrativo ou não implementado

As outras nove páginas conservam dados demonstrativos em `ui/demo/data.py` e
constantes inline. Seus gráficos/valores não são calculados de carteiras
persistidas. Os outros formulários continuam demonstrativos.

Não há edição/exclusão/comparação real de carteiras, ledger persistente,
compras/vendas pela UI, API de mercado, alertas, metas, planejamento, relatórios,
IA ou notificações funcionais. Asset, Transaction, TransactionType, Position,
saldo e custo médio existem e são testados somente no domínio em memória.
O parser de transações permanece deliberadamente inalterado.

`infrastructure/database/` é o local oficial da persistência SQL.
`infrastructure/persistence/` permanece vazio. Não há Alembic ou tabelas
antecipadas.

## Testado em 05/10/2026

- Windows, Python 3.14.0, PySide6/Qt 6.11.2 e SQLAlchemy 2.1.3;
- instalação editável com runtime/dev em `.venv` inicialmente sem dependências;
- 43 testes aprovados: 11 Domain, 6 Application, 7 banco, 19 UI;
- os 9 smoke tests anteriores foram preservados;
- UI cria no SQLite temporário e reabre com novo repositório/janela;
- falha após flush provoca rollback e permite nova gravação;
- Ruff, mypy, compileall e pip check aprovados;
- processos offscreen distintos criam nomes iguais e reabrem por ID;
- iniciar de outra pasta cria/carrega o banco padrão sem traceback;
- página Carteiras renderizada e inspecionada com o backend nativo Windows,
  sem exibir a janela na tela.

A renderização offscreen no Windows não reproduziu as fontes nativas; o backend
Windows renderizou os textos corretamente. Escalas de tela e uso interativo
prolongado continuam pendentes.

## Próximas pendências

1. Incremento 03: persistir ledger Transaction por carteira, sem Position no banco.
2. Incremento 04: integrar compra/venda e consultas por carteira selecionada na UI.
3. Selecionar e integrar o provedor de mercado.
4. Migrar gradualmente as demais páginas para resultados da Application.
5. Validar interface em escalas/monitores distintos.
6. Registrar proposta aprovada, calendário e tratamento acadêmico de A-008.

Permanecem indefinidos o papel de `core/`, a estratégia assíncrona de mercado
e a distribuição executável. Não foram adicionados controllers, viewmodels,
serviços genéricos ou frameworks de injeção.

## Incremento 02 — testado em 06/10/2026

- Asset, TransactionType (BUY/SELL), Transaction e Position imutáveis implementados.
- Invariantes com Decimal finito, sem conversão implícita ou quantize.
- Replay independente por carteira/ativo, com ordenação estável.
- Custo médio ponderado, taxas, venda parcial, lucro/prejuízo, zeragem e recompra.
- positions contém abertas; closed_positions preserva resultado realizado.
  Ambas são tuplas de snapshots imutáveis.
- Contexto Decimal local previsível, mínimo 50 dígitos e precisão ampliável.
- Nenhuma alteração em Portfolio, Application, Infrastructure ou UI.
- 159 testes coletados/aprovados, zero falhas: 116 novos e 43 anteriores preservados.
- Ruff, mypy src, compileall e git diff --check aprovados.
- Regras e ordenação em [DOMAIN_MODEL.md](../02_architecture/DOMAIN_MODEL.md).
