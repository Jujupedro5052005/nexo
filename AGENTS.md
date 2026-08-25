# Nexo — Codex Development Instructions

## Project

Nexo é uma aplicação desktop de investimentos e planejamento financeiro
desenvolvida como projeto acadêmico de Programação Orientada a Objetos.

## Source of truth

Antes de realizar mudanças significativas, consulte:

1. `docs/00_project/PROJECT_OVERVIEW.md`
2. `docs/00_project/REQUIREMENTS.md`
3. `docs/00_project/SCOPE.md`
4. `docs/00_project/ROADMAP.md`
5. `docs/02_architecture/ARCHITECTURE.md`
6. `docs/03_design/DESIGN_SYSTEM.md`
7. `docs/04_development/CODING_STANDARDS.md`
8. `docs/06_progress/CURRENT_STATUS.md`

Os requisitos acadêmicos definidos pelo professor têm prioridade.

## Dependency rules

O projeto deve manter separação entre:

- UI: telas e componentes PySide6;
- Application: casos de uso e coordenação das ações;
- Domain: entidades e regras de negócio;
- Infrastructure: banco de dados, APIs externas e notificações.

Regras:

- a UI não acessa diretamente o banco de dados;
- a UI não faz chamadas HTTP diretamente;
- regras de negócio não ficam dentro das telas;
- o domínio não depende de PySide6;
- acesso ao banco deve ficar na camada de infraestrutura;
- integração com APIs externas deve ficar na camada de infraestrutura.

## Object-oriented programming

O projeto é avaliado em uma disciplina de POO.

Utilizar de forma justificável:

- encapsulamento;
- abstração;
- composição;
- herança quando apropriada;
- polimorfismo;
- interfaces;
- responsabilidade única.

Não criar abstrações artificiais apenas para demonstrar um conceito.

## Workflow

Antes de implementar uma feature:

1. verificar requisitos;
2. verificar arquitetura existente;
3. identificar módulos afetados;
4. implementar a menor alteração coerente;
5. criar ou atualizar testes;
6. executar testes;
7. atualizar documentação se necessário.

## Never

Nunca:

- colocar API keys no código;
- commitar `.env`;
- apagar testes apenas para obter build verde;
- alterar arquitetura silenciosamente;
- duplicar regras de negócio;
- misturar UI, banco e regras de negócio na mesma classe.

## Current work

Sempre verifique:

`docs/06_progress/CURRENT_STATUS.md`

antes de iniciar uma tarefa significativa.
