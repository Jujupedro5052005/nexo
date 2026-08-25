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
- Definition of Done e backlog priorizado do CORE;
- arquitetura didática em UI, Application, Domain e Infrastructure;
- regras de dependência e fluxos técnicos de compra, venda e dashboard;
- modelo de domínio com transações como fonte de verdade;
- schema SQLite inicial e isolamento do SQLAlchemy;
- decisão de não usar Controller/ViewModel, hierarquias de ativos ou posições
  persistidas no CORE.

## Decisão de escopo vigente

O CORE é uma aplicação local de carteira simulada com compra, venda, posição,
preço médio, histórico SQLite e dashboard de custo/alocação. Ele deve funcionar
sem internet. API de cotações e rentabilidade pertencem ao MVP EXTENDED.

Valuation, notificações externas, planejamento financeiro, receitas/despesas,
objetivos e educação financeira estão fora da entrega inicial.

## Em andamento

- confirmação da proposta aprovada e do calendário acadêmico;
- definição do fluxo visual e do design mínimo;
- validação do ambiente Python/PySide6 no Windows.

## Próximas tarefas

1. obter/registrar proposta aprovada e confirmar o ano das datas;
2. desenhar os fluxos visuais F-01 a F-04 e o design mínimo;
3. validar o ambiente PySide6 no Windows;
4. revisar exemplos numéricos de compra, venda e preço médio;
5. somente então iniciar a vertical slice F-01.

## Bloqueios e riscos

- aprovação da proposta ainda não está registrada;
- o ano do cronograma do professor não está confirmado;
- qualquer antecipação da API ou de módulos futuros pode reabrir o risco de
  escopo excessivo.

## Regra de execução

Não iniciar MVP EXTENDED ou OPTIONAL antes do CORE cumprir seu gate. Não
iniciar código de negócio enquanto as decisões de domínio necessárias à
primeira vertical slice não estiverem documentadas.
