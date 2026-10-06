# Roadmap acadêmico do Nexo Invest

As fases são sequenciais o suficiente para proteger o núcleo, mas podem ter
atividades de design e teste em paralelo quando não criarem dependências falsas.

## 0 — Arquitetura e validação acadêmica

- [x] analisar requisitos e criar rastreabilidade inicial;
- [x] definir arquitetura, ledger de transações e posições derivadas;
- [x] alinhar documentação a múltiplas carteiras;
- [ ] registrar proposta aprovada e confirmar o calendário;
- [x] definir `infrastructure/database/` como local oficial da persistência SQL;
- [ ] resolver o papel de `core` e papéis opcionais da UI;

## 1 — Estrutura visual e telas

- [x] definir design system e diretrizes mínimas;
- [x] documentar fluxos principais;
- [x] executar PySide6 no Windows e validar carteiras em offscreen;
- [x] construir shell navegável e estado vazio de carteiras;
- [ ] validar todas as páginas visualmente em diferentes escalas.

## 2 — Implementar domínio e persistência

- [x] implementar `Portfolio` com identidade e nome validados;
- [x] implementar `Asset`, `Transaction`, `TransactionType` e `Position`;
- [x] cobrir invariantes e cálculos com testes unitários;
- [x] implementar persistência estrutural de carteiras;
- [x] implementar ledger de transações por carteira;
- [x] reconstruir posições sem tabela própria;
- [x] testar SQLite, mapeamento de Portfolio, reabertura e rollback;
- [x] testar mapeamento do ledger e preservação decimal.

## 3 — Dados de mercado

- [x] selecionar provedor e documentar restrições;
- [x] definir contrato mínimo e adaptador externo;
- [x] tratar timeout, limites, erros e credenciais;
- [x] testar a integração sem tornar a suíte dependente da internet.

## 4 — Carteiras completas

- [x] criar, listar e selecionar carteiras por ID;
- [ ] atualizar e excluir carteiras conforme políticas definidas;
- [x] registrar compras e vendas;
- [x] carregar histórico e posições reconstruídas;
- [ ] comparar carteiras;
- [ ] validar fluxos completos no Windows.

## 5 — Dashboard e análise

- [x] implementar KPIs, gráfico de custo/valor e histórico real de ativo;
- [ ] implementar evolução histórica da carteira e benchmarks;
- [x] integrar valuation de `calculations`;
- [ ] integrar indicadores adicionais priorizados;
- [x] exibir valor atual e rentabilidade quando houver dados;
- [ ] revisar usabilidade e consistência visual.

## 6 — Alertas

- [ ] persistir `PriceAlert` se priorizado;
- [ ] avaliar condições e exibir alertas dentro do aplicativo;
- [ ] manter notificações externas fora desta fase inicial.

## 7 — Funcionalidades complementares

- [ ] avaliar planejamento e educação financeira;
- [ ] avaliar projeções, risco e valuation adicionais;
- [ ] avaliar IA, mensagens e outras integrações somente com caso de uso e prazo.

## 8 — Testes e entrega

- [x] executar testes unitários, de integração e UI do incremento 01;
- [x] atualizar rastreabilidade com evidências do incremento 01;
- [x] documentar instalação editável e execução reais;
- [ ] preparar e ensaiar demonstração e explicações técnicas;
- [ ] validar checklist final e artefatos confirmados pelo professor.

## Sequência dos incrementos funcionais

1. Concluído: Portfolio persistente e criação/listagem/seleção pela UI.
2. Concluído: domínio financeiro e reconstrução determinística em memória.
3. Concluído: ledger persistente e fluxo completo de compra/venda pela UI,
   histórico, posições e métricas a custo. Escopo ampliado inclui o antigo 04.
4. Concluído: mercado brapi v2, valuation, busca/histórico real e dashboard.
5. Próximo sugerido: comparação real de carteiras por métricas documentadas,
   estados de disponibilidade e moedas; não implementado neste incremento.
