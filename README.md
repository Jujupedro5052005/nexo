# Nexo Invest

**Simulador e Plataforma de Análise de Investimentos** desenvolvido como
projeto acadêmico de Programação Orientada a Objetos.

O Nexo Invest é uma aplicação desktop educacional para pesquisar ativos, criar
múltiplas carteiras simuladas, registrar compras e vendas e analisar resultados.
Não executa ordens reais, não mantém custódia e não oferece recomendação
personalizada.

## Funcionalidades previstas

- consulta de ativos e dados de mercado;
- múltiplas carteiras simuladas e comparação entre elas;
- histórico de compras e vendas;
- posições e preço médio reconstruídos das transações;
- dashboards, gráficos, indicadores e análises;
- alertas no aplicativo quando essa etapa for priorizada.

Planejamento financeiro, educação, IA e notificações externas são extensões,
não requisitos do primeiro núcleo funcional.

## Arquitetura e stack

O projeto usa Python, PySide6, SQLite, SQLAlchemy ou mecanismo equivalente,
`httpx` e pytest. A UI chama casos de uso da Application; o Domain contém
conceitos e regras; Calculations concentra cálculos financeiros; Infrastructure
implementa banco e integrações; `main.py` compõe as dependências.

```text
src/nexo/
├── application/
├── calculations/
├── core/
├── domain/
├── infrastructure/
├── ui/
└── main.py
```

## Status

O projeto está em fase de fundação. A estrutura de diretórios e as decisões
principais estão documentadas, mas os módulos permanecem majoritariamente
vazios e a aplicação ainda não é funcional. Por isso não há comando de execução
publicado neste momento.

## Documentação

- [visão geral](docs/00_project/PROJECT_OVERVIEW.md);
- [requisitos](docs/00_project/REQUIREMENTS.md) e
  [escopo](docs/00_project/SCOPE.md);
- [arquitetura](docs/02_architecture/ARCHITECTURE.md) e
  [modelo de domínio](docs/02_architecture/DOMAIN_MODEL.md);
- [ambiente](docs/04_development/ENVIRONMENT.md) e
  [desenvolvimento](docs/04_development/DEVELOPMENT_GUIDE.md);
- [status atual](docs/06_progress/CURRENT_STATUS.md) e
  [backlog](docs/06_progress/BACKLOG.md).
