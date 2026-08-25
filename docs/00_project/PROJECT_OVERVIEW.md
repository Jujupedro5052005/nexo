# Visão geral do projeto — Nexo Invest

## Produto

**Nexo Invest — Simulador e Plataforma de Análise de Investimentos** é uma
aplicação desktop acadêmica, desenvolvida principalmente em Python e PySide6.
Seu propósito é oferecer um ambiente educacional para organizar estratégias e
analisar investimentos simulados, sem executar operações financeiras reais.

## Problema e proposta

Informações de mercado, históricos de operação e métricas de carteira costumam
ficar dispersos. O Nexo Invest reúne esses dados em uma interface local na qual
o usuário pode pesquisar ativos, manter carteiras separadas, registrar operações
simuladas e visualizar resultados compreensíveis.

## Objetivos principais

- consultar ativos e dados de mercado;
- criar, nomear e selecionar múltiplas carteiras;
- registrar compras e vendas simuladas;
- reconstruir posições a partir das transações;
- acompanhar e comparar carteiras;
- apresentar dashboards, gráficos, indicadores e análises.

O histórico de `Transaction` é a fonte principal de verdade financeira.
`Portfolio` possui identidade e nome persistidos; `Position` e métricas
consolidadas são derivadas. Isso favorece auditoria e consistência.

## Diferenciais

- separação clara entre históricos de estratégias diferentes;
- rastreabilidade das posições até as operações que as originaram;
- cálculos financeiros independentes da interface;
- arquitetura orientada a objetos testável e adequada ao contexto acadêmico.

## Tecnologias previstas

- Python e PySide6;
- SQLite e SQLAlchemy ou mecanismo equivalente;
- serviços externos de dados financeiros por adaptadores;
- bibliotecas de gráficos e análise;
- pytest e ferramentas de qualidade.

## Arquitetura resumida

UI apresenta dados e chama a Application; Application coordena casos de uso;
Domain contém modelos e regras; Calculations reúne cálculos reutilizáveis;
Infrastructure implementa banco e integrações; `main.py` conecta as
implementações. Consulte [`ARCHITECTURE.md`](../02_architecture/ARCHITECTURE.md).

## Escopo

O núcleo prioriza mercado, múltiplas carteiras, transações, posições derivadas,
persistência, dashboards, comparação e análise. Alertas externos, planejamento
financeiro, educação financeira, IA e integrações adicionais são complementares.
Os limites estão em [`SCOPE.md`](SCOPE.md).

O sistema não negocia com corretoras, não mantém custódia, não promete retorno
e não fornece recomendação financeira personalizada.
