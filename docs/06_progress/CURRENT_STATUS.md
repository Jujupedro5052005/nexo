# Status atual do projeto

## Fase atual

**Fundação documental e arquitetural.**

## Definido

- propósito educacional e de simulação, sem operações reais;
- aplicação desktop com Python/PySide6 e persistência SQLite;
- separação UI, Application, Domain, Calculations e Infrastructure;
- suporte a múltiplas carteiras com `id` e `name` persistidos;
- `Transaction` como ledger e `Position` como estado derivado;
- `Asset` como objeto de valor sem hierarquia por categoria;
- composição como relacionamento interno enfatizado;
- herança apenas se houver especialização real;
- integração de mercado por contrato e adaptador;
- recursos complementares fora do núcleo inicial.

## Estruturado

As árvores de `src/nexo/` e `tests/` existem, mas quase todas as subpastas
contêm somente `.gitkeep`. Há `__init__.py`, `main.py` e `tests/conftest.py`, sem
implementação funcional correspondente aos módulos documentados.

## Em implementação

Nenhuma funcionalidade foi identificada como em implementação no estado atual
dos arquivos rastreados.

## Implementado

Somente scaffolding Python mínimo. Não há modelos de domínio, casos de uso,
repositórios, adaptadores, telas ou cálculos implementados.

## Testado

Não foram encontrados testes funcionais, unitários, de integração ou de UI além
da estrutura preparada.

## Pendências imediatas

1. registrar proposta aprovada e confirmar ano/calendário;
2. confirmar com o professor o tratamento acadêmico do requisito A-008;
3. definir design visual e wireflows;
4. validar ambiente PySide6 no Windows;
5. implementar modelos do domínio e persistência de `Portfolio`/`Transaction`;
6. reconstruir `Position` e criar os primeiros casos de uso testados.

## Ambiguidades

- responsabilidade de `src/nexo/core/`;
- fronteira entre `infrastructure/database/` e `infrastructure/persistence/`;
- distinção prática entre `ui/components` e `ui/widgets`;
- uso efetivo de `controllers` e `viewmodels`;
- provedor de mercado e estratégia assíncrona;
- conteúdo e data da aprovação acadêmica.

Este documento descreve evidência real. Diretório preparado ou decisão
documentada não equivale a funcionalidade implementada.
