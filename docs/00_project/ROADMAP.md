# Roadmap acadêmico do Nexo Invest

As fases são sequenciais o suficiente para proteger o núcleo, mas podem ter
atividades de design e teste em paralelo quando não criarem dependências falsas.

## 0 — Arquitetura e validação acadêmica

- [x] analisar requisitos e criar rastreabilidade inicial;
- [x] definir arquitetura, ledger de transações e posições derivadas;
- [x] alinhar documentação a múltiplas carteiras;
- [ ] registrar proposta aprovada e confirmar o calendário;
- [ ] resolver fronteiras ainda ambíguas (`core`, `persistence`, componentes de UI);

## 1 — Estrutura visual e telas

- [ ] definir design system e diretrizes mínimas;
- [ ] detalhar fluxos e wireflows;
- [ ] validar o ambiente PySide6 no Windows;
- [ ] construir shell e telas essenciais com estados vazios.

## 2 — Implementar domínio e persistência

- [ ] implementar `Asset`, `Portfolio`, `Transaction`, `TransactionType` e `Position`;
- [ ] cobrir invariantes e cálculos com testes unitários;
- [ ] implementar persistência estrutural de carteiras;
- [ ] implementar ledger de transações por carteira;
- [ ] reconstruir posições sem tabela própria;
- [ ] testar SQLite e mapeamentos de domínio/ORM.

## 3 — Dados de mercado

- [ ] selecionar provedor e documentar restrições;
- [ ] definir contrato mínimo e adaptador externo;
- [ ] tratar timeout, limites, erros e credenciais;
- [ ] testar a integração sem tornar a suíte dependente da internet.

## 4 — Carteiras completas

- [ ] criar, atualizar, selecionar e excluir carteiras;
- [ ] registrar compras e vendas;
- [ ] carregar histórico e posições reconstruídas;
- [ ] comparar carteiras;
- [ ] validar fluxos completos no Windows.

## 5 — Dashboard e análise

- [ ] implementar métricas e gráficos funcionais;
- [ ] integrar indicadores priorizados de `calculations`;
- [ ] exibir valor atual e rentabilidade quando houver dados;
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

- [ ] executar testes unitários, de integração e de UI aplicáveis;
- [ ] atualizar rastreabilidade com evidências;
- [ ] documentar instalação e execução reais;
- [ ] preparar e ensaiar demonstração e explicações técnicas;
- [ ] validar checklist final e artefatos confirmados pelo professor.
