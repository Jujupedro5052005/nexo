# Backlog priorizado

## P0 — Validação e desenho

- [ ] Registrar proposta aprovada e escopo aceito.
- [ ] Confirmar calendário e tratamento acadêmico de A-008 com o professor.
- [ ] Definir wireflows e design system mínimo.
- [ ] Validar PySide6 no Windows.
- [ ] Delimitar `core`, `infrastructure/persistence` e papéis opcionais da UI.

## P1 — Domínio e cálculos fundamentais

- [ ] Implementar `Asset` como objeto de valor.
- [ ] Implementar `Portfolio` com `id` e `name`.
- [ ] Implementar `TransactionType` e `Transaction` vinculada à carteira.
- [ ] Implementar `Position` derivada e reconstrução do ledger.
- [ ] Definir e testar preço médio, venda, precisão e arredondamento com `Decimal`.

## P1 — Persistência

- [ ] Definir schema de `portfolios` e `transactions`.
- [ ] Implementar `PortfolioRepository` concreto.
- [ ] Implementar `TransactionRepository` por carteira.
- [ ] Mapear modelos ORM sem contaminar Domain/Application.
- [ ] Testar atomicidade, reabertura, vínculo e preservação decimal.

## P1 — Casos de uso de carteira

- [ ] Criar, atualizar, excluir e listar carteiras.
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

- [ ] Implementar shell, navegação e seleção explícita de carteira.
- [ ] Implementar formulários de carteira, compra e venda.
- [ ] Exibir histórico, posições e estados vazios.
- [ ] Integrar mercado sem HTTP direto.
- [ ] Cobrir fluxos críticos com pytest-qt e roteiro Windows.

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
- [ ] Documentar instalação/execução quando funcionarem.
- [ ] Preparar demonstrações e explicações técnicas.
- [ ] Validar checklist final no Windows.
