# Nexo Invest

**Simulador e Plataforma de Análise de Investimentos**, desenvolvido para a
disciplina de Programação Orientada a Objetos.

Aplicação desktop educacional e de simulação. Não executa ordens reais,
não mantém custódia e não oferece recomendação personalizada.

## Status

**Incremento funcional 01: criar, listar e selecionar carteiras persistentes.**
A página Carteiras usa dados reais de `Portfolio`, aceita nomes iguais com IDs
distintos e preserva as carteiras após reinício. A seleção vive somente na
sessão atual. Carteiras vazias não exibem métricas fictícias.

As outras nove páginas continuam demonstrativas. Transações, posições,
cálculos financeiros, mercado, comparação, edição e exclusão de carteiras
ainda não foram implementados.

## Funcionalidades previstas

- consulta de ativos e dados de mercado;
- múltiplas carteiras simuladas e comparação;
- histórico de compras e vendas;
- posições e preço médio reconstruídos das transações;
- dashboards, gráficos, indicadores e análises;
- alertas no aplicativo quando essa etapa for priorizada.

Planejamento, educação, IA e notificações externas são complementos futuros.

## Arquitetura

```text
UI -> Application -> Domain + PortfolioRepository
                                  ^
                 SqlAlchemyPortfolioRepository -> SQLite

main.py compõe as dependências.
```

O primeiro fluxo usa Python, PySide6, SQLite e SQLAlchemy. Calculations está
reservada aos cálculos futuros. HTTP e outras integrações ainda não existem.

## Instalação e execução

Requer Python >=3.10 compatível com PySide6. Na raiz do clone, no Windows:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m nexo.main
```

Para desenvolvimento:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

No Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e .
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m nexo.main
```

`requirements.txt` é a fonte única das dependências de execução, lida pelo
setuptools em `pyproject.toml`. O banco `data/nexo.db` é criado na raiz deste
checkout, independentemente da pasta de onde a aplicação é iniciada. O `.env`
não é necessário nem carregado neste incremento.

## Verificações

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m compileall -q src tests bootstrap_project.py
Remove-Item Env:QT_QPA_PLATFORM
```

No Linux: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest`.

## Documentação

- [visão geral](docs/00_project/PROJECT_OVERVIEW.md);
- [requisitos](docs/00_project/REQUIREMENTS.md) e [escopo](docs/00_project/SCOPE.md);
- [arquitetura](docs/02_architecture/ARCHITECTURE.md) e [domínio](docs/02_architecture/DOMAIN_MODEL.md);
- [ambiente](docs/04_development/ENVIRONMENT.md) e [testes](docs/04_development/TESTING.md);
- [status](docs/06_progress/CURRENT_STATUS.md) e [backlog](docs/06_progress/BACKLOG.md).
