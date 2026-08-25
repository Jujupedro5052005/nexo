# Visão geral do projeto — Nexo

## Propósito

O Nexo é uma aplicação desktop acadêmica, desenvolvida em Python com PySide6,
para acompanhar uma carteira de investimentos exclusivamente simulada. O
projeto existe para demonstrar uma solução funcional, coerente e orientada a
objetos, com regras de domínio testáveis, interface gráfica e integração
prática com armazenamento de dados.

## Entrega inicial

O CORE MVP permite:

- registrar compras e vendas simuladas;
- consultar posições, custo e preço médio;
- consultar o histórico persistido de transações;
- visualizar custo total e alocação por ativo em dashboard;
- fechar e reabrir a aplicação sem perder os dados.

O CORE usa SQLite como integração acadêmica obrigatória e funciona sem
internet. Consulta de cotações por API e rentabilidade de mercado pertencem ao
MVP EXTENDED e só devem começar depois do núcleo estável.

## Módulos por horizonte

### CORE MVP

- Carteira;
- Transações simuladas;
- Posições e preço médio;
- Histórico;
- Dashboard mínimo;
- Persistência.

### MVP EXTENDED

- Mercado e cotações por API;
- Valor de mercado e rentabilidade.

### OPTIONAL

- Indicadores financeiros selecionados;
- Alertas de preço dentro da aplicação.

### FUTURE / OUT OF SCOPE da entrega inicial

- valuation e preço teto;
- notificações por e-mail ou WhatsApp;
- planejamento financeiro, receitas, despesas e objetivos;
- educação financeira;
- integrações adicionais.

## Limites importantes

O Nexo utiliza somente carteiras simuladas. O sistema não executa ordens reais,
não se conecta a corretoras para negociação, não mantém custódia e não oferece
recomendação personalizada nem promessa de retorno.

O escopo detalhado, os fluxos e a Definition of Done estão em
`docs/00_project/SCOPE.md`.
