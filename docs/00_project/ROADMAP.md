# Roadmap acadêmico do Nexo

Este roadmap prioriza uma demonstração funcional e coerente. As fases são
gates: trabalho opcional não antecipa o núcleo.

## Fase 0 — Fundação e validação acadêmica

- [x] analisar os requisitos do professor;
- [x] criar rastreabilidade acadêmica;
- [x] definir e classificar o MVP;
- [ ] registrar proposta aprovada e confirmar o calendário;
- [ ] detalhar arquitetura e dependências entre camadas;
- [ ] definir modelo de domínio, invariantes e precisão monetária;
- [ ] definir schema/migração inicial do banco;
- [ ] definir fluxo visual e design system mínimo;
- [ ] validar ambiente Python/PySide6 no Windows.

**Gate:** proposta confirmada e arquitetura capaz de sustentar F-01 sem violar
as regras de dependência.

## Fase 1 — Primeira vertical slice: compra persistida

- [ ] criar carteira local e ativo;
- [ ] registrar compra por caso de uso;
- [ ] persistir transação em SQLite;
- [ ] exibir histórico e posição na UI;
- [ ] reabrir aplicação preservando dados;
- [ ] testar domínio e persistência.

**Gate:** fluxo F-01 completo, demonstrável e testado.

## Fase 2 — Núcleo de negociação simulada

- [ ] suportar múltiplas compras e preço médio ponderado;
- [ ] implementar venda parcial/total;
- [ ] rejeitar venda acima da quantidade disponível;
- [ ] consolidar posições e histórico;
- [ ] completar validações e estados vazios;
- [ ] cobrir F-02 e F-03 com testes.

**Gate:** regras do domínio consistentes e nenhuma persistência parcial em erro.

## Fase 3 — Dashboard e acabamento do CORE

- [ ] exibir custo total da carteira;
- [ ] criar gráfico funcional de alocação por custo;
- [ ] atualizar dashboard após transações;
- [ ] revisar organização, clareza, usabilidade e estética;
- [ ] validar F-04 no Windows;
- [ ] cumprir toda a Definition of Done do CORE.

**Gate:** CORE MVP funcional, offline, testado e apresentável.

## Fase 4 — MVP EXTENDED

Somente após o gate da Fase 3:

- [ ] escolher e documentar provedor de mercado;
- [ ] implementar contrato e adaptador de cotações;
- [ ] tratar configuração, timeout, erros e limites;
- [ ] consultar ativos/cotações sem acoplar UI a HTTP;
- [ ] calcular valor de mercado e rentabilidade;
- [ ] manter fallback coerente quando a API estiver indisponível.

## Fase 5 — OPTIONAL

Somente se o CORE estiver pronto e o prazo permitir:

- [ ] selecionar um conjunto pequeno de indicadores financeiros;
- [ ] implementar alertas configuráveis de preço dentro da aplicação;
- [ ] avaliar se o diferencial melhora a apresentação sem ameaçar estabilidade.

## Fase 6 — Entrega acadêmica

- [ ] atualizar rastreabilidade com evidências;
- [ ] documentar instalação e execução;
- [ ] preparar conteúdo exigido para apresentação parcial/final;
- [ ] preparar e ensaiar os fluxos F-01 a F-04;
- [ ] ensaiar explicação de arquitetura, POO, classes, integração e limitações;
- [ ] executar testes e checklist final em Windows;
- [ ] confirmar apenas com o professor eventuais artefatos não citados no PDF.

## Pós-MVP / fora da entrega inicial

- valuation e preço teto;
- notificações por e-mail ou WhatsApp;
- planejamento financeiro, receitas, despesas e objetivos;
- educação financeira;
- integrações adicionais sem caso de uso aprovado;
- operações reais ou integração de negociação com corretoras.
