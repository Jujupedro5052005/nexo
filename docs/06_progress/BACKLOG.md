# Backlog priorizado

Os itens seguem `docs/00_project/SCOPE.md`. Dependências entre colchetes devem
estar concluídas antes do item.

## P0 — Bloqueios acadêmicos e arquitetura

- [x] B-001 — Consolidar requisitos acadêmicos e rastreabilidade.
- [x] B-002 — Definir classificação e CORE MVP. [B-001]
- [ ] B-003 — Registrar proposta aprovada, escopo aceito e data. [B-002]
- [ ] B-004 — Confirmar ano/calendário das entregas com o professor.
- [ ] B-005 — Detalhar arquitetura das camadas e regras de dependência. [B-002]
- [ ] B-006 — Modelar `Carteira`, `Ativo`, `Transação` e `Posição`, relações e invariantes. [B-005]
- [ ] B-007 — Definir semântica de venda, preço médio, arredondamento e tipo decimal. [B-006]
- [ ] B-008 — Definir contrato de repositório e schema SQLite inicial. [B-006]
- [ ] B-009 — Definir wireflows F-01 a F-04 e design mínimo. [B-002]
- [ ] B-010 — Validar instalação e execução de PySide6 no Windows.

## P1 — CORE MVP: vertical slice F-01

- [ ] B-101 — Implementar domínio mínimo de carteira, ativo, compra e posição. [B-006, B-007]
- [ ] B-102 — Implementar repositório SQLite para transações. [B-008]
- [ ] B-103 — Implementar caso de uso de registrar compra. [B-101, B-102]
- [ ] B-104 — Implementar UI mínima de registro de compra. [B-009, B-103]
- [ ] B-105 — Exibir histórico e posição persistidos. [B-102, B-104]
- [ ] B-106 — Testar domínio, persistência e reinício da aplicação. [B-105]

## P1 — CORE MVP: regras F-02 e F-03

- [ ] B-111 — Implementar múltiplas compras e preço médio ponderado. [B-101]
- [ ] B-112 — Implementar venda parcial e total. [B-111]
- [ ] B-113 — Rejeitar venda acima da posição sem alterar dados. [B-112]
- [ ] B-114 — Consolidar histórico e posições na UI. [B-105, B-113]
- [ ] B-115 — Cobrir regras e casos de erro com testes. [B-111, B-113]

## P1 — CORE MVP: dashboard e conclusão

- [ ] B-121 — Calcular custo total e alocação por custo. [B-114]
- [ ] B-122 — Implementar dashboard e gráfico funcional. [B-009, B-121]
- [ ] B-123 — Atualizar dashboard após transações. [B-122]
- [ ] B-124 — Revisar validações, mensagens, estado vazio e usabilidade. [B-114, B-123]
- [ ] B-125 — Validar F-01 a F-04 em Windows. [B-124]
- [ ] B-126 — Cumprir e auditar a Definition of Done do CORE. [B-125]

## P2 — MVP EXTENDED

- [ ] B-201 — Selecionar provedor de cotações e documentar restrições. [B-126]
- [ ] B-202 — Definir contrato de provedor e adaptador HTTP. [B-201]
- [ ] B-203 — Implementar consulta com timeout, erros, limites e fallback. [B-202]
- [ ] B-204 — Exibir cotação atual na UI. [B-203]
- [ ] B-205 — Calcular valor de mercado e rentabilidade. [B-204]
- [ ] B-206 — Testar integração sem depender da API real na suíte comum. [B-203]

## P3 — OPTIONAL

- [ ] B-301 — Selecionar indicadores financeiros de baixo risco. [B-206]
- [ ] B-302 — Implementar indicadores selecionados. [B-301]
- [ ] B-303 — Implementar alerta de preço dentro da aplicação. [B-203]

## FUTURE / OUT OF SCOPE

- [ ] F-001 — Valuation e preço teto.
- [ ] F-002 — Notificações por e-mail ou WhatsApp.
- [ ] F-003 — Planejamento financeiro pessoal.
- [ ] F-004 — Receitas e despesas.
- [ ] F-005 — Objetivos financeiros.
- [ ] F-006 — Educação financeira.
- [ ] F-007 — Integrações adicionais com caso de uso futuro.

Itens FUTURE não devem ser puxados durante o MVP sem revisão explícita de
escopo e impacto no prazo.
