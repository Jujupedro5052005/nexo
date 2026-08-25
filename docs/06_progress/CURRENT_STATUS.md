# Status atual do projeto

## Fase atual

**Fase 0 — Fundação e validação acadêmica**

## Concluído

- conceito inicial e nome Nexo;
- estrutura inicial do repositório;
- leitura dos requisitos oficiais e materiais de aula;
- consolidação dos requisitos acadêmicos A-001 a A-023;
- matriz de rastreabilidade inicial;
- definição do CORE MVP, MVP EXTENDED, OPTIONAL e FUTURE;
- definição dos fluxos F-01 a F-04;
- Definition of Done e backlog priorizado do CORE.

## Decisão de escopo vigente

O CORE é uma aplicação local de carteira simulada com compra, venda, posição,
preço médio, histórico SQLite e dashboard de custo/alocação. Ele deve funcionar
sem internet. API de cotações e rentabilidade pertencem ao MVP EXTENDED.

Valuation, notificações externas, planejamento financeiro, receitas/despesas,
objetivos e educação financeira estão fora da entrega inicial.

## Em andamento

- confirmação da proposta aprovada e do calendário acadêmico;
- detalhamento da arquitetura;
- definição do modelo de domínio e das regras financeiras;
- definição do schema inicial e do design mínimo.

## Próximas tarefas

1. obter/registrar proposta aprovada e confirmar o ano das datas;
2. detalhar arquitetura e dependências entre camadas;
3. modelar carteira, ativo, transação e posição;
4. definir preço médio, venda, precisão e arredondamento;
5. definir contrato de repositório e schema SQLite;
6. desenhar os fluxos F-01 a F-04;
7. validar o ambiente PySide6 no Windows;
8. somente então iniciar a vertical slice F-01.

## Bloqueios e riscos

- aprovação da proposta ainda não está registrada;
- o ano do cronograma do professor não está confirmado;
- arquitetura e modelo de domínio ainda não estão detalhados;
- qualquer antecipação da API ou de módulos futuros pode reabrir o risco de
  escopo excessivo.

## Regra de execução

Não iniciar MVP EXTENDED ou OPTIONAL antes do CORE cumprir seu gate. Não
iniciar código de negócio enquanto as decisões de domínio necessárias à
primeira vertical slice não estiverem documentadas.
