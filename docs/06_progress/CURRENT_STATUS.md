# Status atual do projeto

## Fase atual

**Fundação executável e protótipo visual completo da aplicação desktop.**

## Implementado

- pacote instalável em modo editável e entry point `python -m nexo.main`;
- janela PySide6 redimensionável com sidebar e topbar fixas;
- tema dark centralizado e ícones vetoriais próprios;
- navegação por `QStackedWidget` entre dez páginas;
- páginas visuais de Visão Geral, Carteiras, Ativos, Movimentações,
  Planejamento, Metas, Alertas, Análises, Relatórios e Configurações;
- gráficos responsivos de linha, barras e donut usando QtCharts;
- tabelas, filtros, seletores, cards, badges, progresso e ações demonstrativas;
- diálogos completos de movimentação, ativo, alerta, meta e carteira;
- feedback visual para ações que ainda dependem das próximas camadas;
- dados de apresentação isolados em `src/nexo/ui/demo/data.py` e identificados
  na interface como demonstrativos.

## Não implementado

Não há modelos de domínio, regras financeiras, casos de uso, SQLAlchemy,
SQLite, provedor de mercado, cotações reais, autenticação, IA, notificações ou
geração de relatórios. Os gráficos e valores exibidos não são calculados a
partir de uma carteira real e não são persistidos.

Salvar nos diálogos apenas mostra o aviso de demonstração. Tema claro, dados
locais, exportação e canais externos permanecem desabilitados ou marcados para
uma etapa futura.

## Testado

- ambiente local: Python 3.10.12, PySide6 6.8.0.2 e Qt 6.8.0 no Linux;
- smoke tests cobrem criação da janela, dez páginas, página inicial, navegação e
  abertura dos quatro diálogos das ações rápidas;
- `compileall`, Ruff e mypy passam;
- inicialização e renderização foram verificadas em modo offscreen;
- execução e aparência no Windows continuam pendentes de validação manual.

## Pendências imediatas

1. validar visualmente o protótipo no Windows e em escalas de tela diferentes;
2. registrar proposta aprovada e confirmar ano/calendário;
3. confirmar com o professor o tratamento acadêmico do requisito A-008;
4. implementar modelos do domínio e persistência de `Portfolio`/`Transaction`;
5. reconstruir `Position` e criar os primeiros casos de uso testados;
6. substituir gradualmente o dataset demonstrativo por resultados da
   Application;
7. selecionar e integrar o provedor real de mercado em etapa posterior.

## Ambiguidades preservadas

- responsabilidade de `src/nexo/core/`;
- fronteira entre `infrastructure/database/` e `infrastructure/persistence/`;
- provedor de mercado e estratégia assíncrona;
- conteúdo e data da aprovação acadêmica.

Este documento distingue interface implementada de funcionalidade financeira.
Uma tela, tabela ou gráfico demonstrativo não comprova domínio, banco ou API.
