# Backlog priorizado

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
- [ ] Definir e implementar schema de `transactions`.
- [x] Implementar abstração e PortfolioRepository SQLAlchemy concreto.
- [ ] Implementar `TransactionRepository` por carteira.
- [x] Mapear Portfolio ORM/domínio sem contaminar Domain/Application.
- [x] Testar rollback e reabertura de carteiras.
- [ ] Testar vínculo de transações e preservação decimal.

## P1 — Casos de uso de carteira

- [x] Criar e listar carteiras pelos casos de uso.
- [ ] Atualizar e excluir carteiras conforme políticas definidas.
- [ ] Registrar compra e venda.
- [ ] Carregar carteira e reconstruir posições.
- [ ] Rejeitar venda insuficiente sem gravação parcial.
- [ ] Comparar carteiras por métricas definidas.

## P1 — Integração de mercado

- [ ] Selecionar provedor e registrar restrições.
- [ ] Definir `MarketDataProvider` mínimo.
- [ ] Implementar adaptador em `infrastructure/market_data/adapters`.
- [ ] Tratar timeout, erros, limites e credenciais.
- [ ] Testar com provider falso e integração separada.

## P1 — UI

- [x] Implementar shell, navegação e seleção explícita de carteira por ID.
- [x] Integrar formulário de criação e estado vazio de carteiras reais.
- [ ] Integrar formulários de compra e venda.
- [ ] Exibir histórico, posições e estados vazios.
- [ ] Integrar mercado sem HTTP direto.
- [x] Cobrir criar/listar/selecionar com pytest-qt e reabertura SQLite.
- [ ] Cobrir fluxos financeiros e roteiro interativo Windows.

## P2 — Dashboard e análise

- [ ] Definir métricas e período de comparação.
- [ ] Implementar dashboard e gráficos funcionais.
- [ ] Integrar cálculos priorizados de `calculations`.
- [ ] Exibir valor atual e rentabilidade quando houver cotação.

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

## Entrega do incremento 02

Domínio e replay concluídos em memória. Rejeição de saldo insuficiente é regra
testada do domínio; caso de uso com garantia de gravação atômica permanece
pendente até o ledger persistente. Arredondamento visual é futuro; o contexto
matemático Decimal local está definido e testado.
