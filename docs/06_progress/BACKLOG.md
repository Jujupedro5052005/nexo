# Backlog priorizado

## Aceite restante — 05.2

- [x] Implementar quatro providers, routing fechado, budgets e snapshot avançado.
- [x] Validar brapi/Yahoo online dentro do smoke limitado; preservar ledger.
- [ ] Configurar BOLSAI_API_KEY local e validar ITSA4 fundamentos/bridge/CVM online.
- [ ] Revisar uso prolongado/DPI das novas áreas e execução com dados CVM reais.

Políticas completas: [DATA_PROVIDERS.md](../02_architecture/DATA_PROVIDERS.md).

## P0 — Validação e desenho

- [ ] Registrar proposta aprovada e escopo aceito.
- [ ] Confirmar calendário e tratamento acadêmico de A-008 com o professor.
- [x] Definir fluxos principais e design system mínimo.
- [x] Validar execução PySide6 e carteiras no Windows.
- [ ] Validar visualmente todas as páginas e escalas de tela.
- [x] Fixar persistência SQL em `infrastructure/database/`.
- [ ] Delimitar `core` e papéis opcionais da UI.

## P1 — Domínio e cálculos fundamentais

- [x] Implementar `Asset` como objeto de valor.
- [x] Implementar `Portfolio` com ID/nome validados e nomes iguais permitidos.
- [x] Implementar `TransactionType` e `Transaction` vinculada à carteira.
- [x] Implementar `Position` derivada e reconstrução do ledger.
- [x] Definir e testar preço médio, venda, precisão e arredondamento com `Decimal`.

## P1 — Persistência

- [x] Implementar schema de `portfolios(id, name)`.
- [x] Definir e implementar schema de `transactions`.
- [x] Implementar abstração e PortfolioRepository SQLAlchemy concreto.
- [x] Implementar `TransactionRepository` por carteira.
- [x] Mapear Portfolio ORM/domínio sem contaminar Domain/Application.
- [x] Testar rollback e reabertura de carteiras.
- [x] Testar vínculo de transações e preservação decimal.

## P1 — Casos de uso de carteira

- [x] Criar e listar carteiras pelos casos de uso.
- [ ] Atualizar e excluir carteiras conforme políticas definidas.
- [x] Registrar compra e venda.
- [x] Carregar carteira e reconstruir posições.
- [x] Rejeitar venda insuficiente sem gravação parcial.
- [ ] Comparar carteiras por métricas definidas.

## P1 — Integração de mercado

- [x] Selecionar provedor e registrar restrições.
- [x] Definir `MarketDataProvider` mínimo.
- [x] Implementar adaptador em `infrastructure/market_data/adapters`.
- [x] Tratar timeout, erros, limites e credenciais.
- [x] Testar com provider falso e integração separada.

## P1 — UI

- [x] Implementar shell, navegação e seleção explícita de carteira por ID.
- [x] Integrar formulário de criação e estado vazio de carteiras reais.
- [x] Integrar formulários de compra e venda.
- [x] Exibir histórico, posições e estados vazios.
- [x] Integrar mercado sem HTTP direto.
- [x] Cobrir criar/listar/selecionar com pytest-qt e reabertura SQLite.
- [ ] Cobrir fluxos financeiros e roteiro interativo Windows.

## P2 — Dashboard e análise

- [x] Definir comparação por ID/fotografia atual, métricas, moedas e disponibilidade.
- [x] Implementar KPIs, custo/valor aberto e gráfico real de ativo.
- [ ] Evolução histórica de carteira, benchmarks e análises adicionais.
- [x] Integrar cálculos priorizados de `calculations`.
- [x] Exibir valor atual e retorno sobre custo aberto quando houver cotação.

## P3 — Alertas

- [ ] Implementar e persistir `PriceAlert` se o prazo permitir.
- [ ] Avaliar condições e exibir alertas no aplicativo.

## P4 — Complementar

- [ ] Planejamento e educação financeira.
- [ ] Projeções, risco e valuation adicionais.
- [ ] Notificações externas.
- [ ] IA e integrações adicionais com caso de uso confirmado.

## Entrega contínua

- [ ] Atualizar testes, documentação, status e rastreabilidade a cada incremento.
- [x] Documentar instalação editável e execução do incremento 01.
- [ ] Preparar demonstrações e explicações técnicas.
- [ ] Validar checklist final no Windows.

## Entrega histórica do incremento 02

Domínio e replay concluídos em memória. Rejeição de saldo insuficiente é regra
testada do domínio; caso de uso com garantia de gravação atômica permanece
pendente até o ledger persistente. Arredondamento visual é futuro; o contexto
matemático Decimal local está definido e testado.

## Grande Incremento 03 entregue

Ledger CREATE/READ, validação integral antes do INSERT, FK, Decimal/datetime
preservados, rollback, schema antigo, formulário financeiro, parser, filtros,
reabertura, posições e resumos reais concluídos. A garantia financeira assume
uma instância escritora local; suporte a escritores concorrentes é futuro.
O item de roteiro interativo Windows/DPI permanece aberto apesar dos testes UI.
Dashboard tem métricas reais, mas gráficos de mercado continuam demonstrativos;
Comparação, edição/exclusão e complementos seguem pendentes. API entregue no 04.


## Grande Incremento 04 entregue

brapi v2, token opcional, HTTP isolado, Decimal direto, batch entre carteiras,
falhas parciais/offline, histórico/busca, valuation BRL e workers Qt com gerações.
Ativos real; Carteiras/Overview com métricas/posições e gráfico de custo/valor.
Sem persistir quotes/valuation, sem conversões de moeda/ticker fictícias.

Próximo incremento recomendado: comparação de carteiras por métricas existentes,
com denominadores, moedas e disponibilidade explícitos. Não implementado aqui.
Cache TTL, escrituras concorrentes, edição/exclusão e cancelamento HTTP instantâneo
somente se caso de uso posterior justificar. Demos complementares ainda pendentes.

## Grande Incremento 05 entregue

Fundamentos reais, indicadores, Graham/Bazin com yield explícito, margem neutra,
risco do ativo, comparação por ID, pesos/maior/top 3/HHI e cache TTL compartilhado.
Ativos/Análises reais e concentração em Carteiras/Overview; sem schema adicional.
Os próximos itens sugeridos na seção 04 são históricos; comparação/cache concluídos.

Próximo recomendado, sem implementação: caixa/aportes/retiradas explícitos, política
de proventos/eventos, avaliações completas para preparar TWR. XIRR/MWR, Sharpe,
benchmarks, edição/exclusão, FX, cancelamento HTTP instantâneo e DPI prolongado
continuam futuros. Requisitos acadêmicos ainda pendentes são preservados.
