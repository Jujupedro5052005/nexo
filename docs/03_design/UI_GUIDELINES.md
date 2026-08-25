# Diretrizes de interface

Este documento trata de usabilidade e consistência. A organização técnica da UI
está em [`UI_ARCHITECTURE.md`](../02_architecture/UI_ARCHITECTURE.md).

- manter a carteira selecionada visível em operações e análises;
- pedir confirmação para ações destrutivas e explicar suas consequências;
- validar campos perto da origem do erro sem apagar entradas do usuário;
- distinguir indisponibilidade de mercado de ausência de posições;
- exibir moeda, data, fonte e horário quando relevantes;
- usar textos diretos e evitar jargão financeiro sem explicação;
- oferecer estados vazios com próxima ação clara;
- manter navegação, títulos, tabelas, formulários e atalhos consistentes;
- não usar apenas cor para indicar ganho, perda, alerta ou seleção;
- preservar responsividade durante chamadas externas;
- nunca exibir SQL, stack traces, chaves ou detalhes internos.

Antes de implementar uma tela, verificar o fluxo correspondente em
[`USER_FLOWS.md`](USER_FLOWS.md) e os tokens aprovados em
[`DESIGN_SYSTEM.md`](DESIGN_SYSTEM.md).
