from pathlib import Path

ROOT = Path(__file__).parent.resolve()

DIRECTORIES = [
    ".github/ISSUE_TEMPLATE",
    ".github/workflows",

    "docs/00_project",
    "docs/01_professor/original_requirements",
    "docs/01_professor/class_material",
    "docs/02_architecture/decisions",
    "docs/02_architecture/diagrams",
    "docs/03_design/assets",
    "docs/04_development",
    "docs/05_delivery",
    "docs/06_progress",

    "src/nexo/core",

    "src/nexo/domain/models",
    "src/nexo/domain/enums",
    "src/nexo/domain/services",
    "src/nexo/domain/interfaces",

    "src/nexo/application/portfolio",
    "src/nexo/application/assets",
    "src/nexo/application/analysis",
    "src/nexo/application/alerts",
    "src/nexo/application/financial_planning",
    "src/nexo/application/education",

    "src/nexo/infrastructure/database/models",
    "src/nexo/infrastructure/database/repositories",
    "src/nexo/infrastructure/database/migrations",
    "src/nexo/infrastructure/market_data/adapters",
    "src/nexo/infrastructure/notifications",
    "src/nexo/infrastructure/persistence",

    "src/nexo/calculations/valuation",
    "src/nexo/calculations/indicators",
    "src/nexo/calculations/projections",
    "src/nexo/calculations/risk",

    "src/nexo/ui/windows",
    "src/nexo/ui/pages",
    "src/nexo/ui/dialogs",
    "src/nexo/ui/widgets",
    "src/nexo/ui/components",
    "src/nexo/ui/controllers",
    "src/nexo/ui/viewmodels",
    "src/nexo/ui/resources/icons",
    "src/nexo/ui/resources/images",
    "src/nexo/ui/styles",

    "tests/unit/domain",
    "tests/unit/calculations",
    "tests/unit/application",
    "tests/integration/database",
    "tests/integration/market_data",
    "tests/integration/notifications",
    "tests/ui",
    "tests/fixtures",

    "scripts",

    "data/sample",
    "data/seeds",

    "assets/branding",
    "assets/screenshots",
    "assets/presentation",

    "deliverables/reports",
    "deliverables/presentations",
    "deliverables/diagrams",
    "deliverables/releases",
]

FILES = {
    "README.md": """# Nexo

Aplicação desktop de investimentos e planejamento financeiro.

Projeto desenvolvido para a disciplina de Programação Orientada a Objetos.

> Projeto em desenvolvimento.

## Tecnologias previstas

- Python
- PySide6
- SQLAlchemy
- SQLite
- APIs externas de mercado financeiro
- pytest

Consulte `AGENTS.md` e a pasta `docs/` para informações sobre arquitetura,
planejamento e desenvolvimento.
""",

    "AGENTS.md": """# Nexo — Codex Development Instructions

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
""",

    ".gitignore": """# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/

# Virtual environments
.venv/
venv/
env/

# Environment variables
.env

# IDE
.vscode/
.idea/

# Tests
.pytest_cache/
.coverage
htmlcov/

# Ruff / mypy
.ruff_cache/
.mypy_cache/

# Database
*.db
*.sqlite
*.sqlite3

# OS
.DS_Store
Thumbs.db

# Temporary
*.log
tmp/
temp/
""",

    ".env.example": """NEXO_DATABASE_URL=sqlite:///data/nexo.db

MARKET_API_KEY=
MARKET_API_BASE_URL=

EMAIL_ADDRESS=
EMAIL_APP_PASSWORD=
""",

    "requirements.txt": """PySide6
SQLAlchemy
httpx
pydantic
python-dotenv
""",

    "requirements-dev.txt": """pytest
pytest-cov
pytest-qt
ruff
mypy
""",

    "pytest.ini": """[pytest]
testpaths = tests
pythonpath = src
""",

    "docs/00_project/PROJECT_OVERVIEW.md": """# Project Overview — Nexo

## Purpose

TODO: descrever visão geral do Nexo.

## Main modules

- Mercado
- Carteira
- Análises
- Alertas
- Planejamento financeiro
- Educação financeira

## Important

O Nexo utiliza carteiras simuladas.

O sistema não executa ordens reais de compra ou venda de ativos.
""",

    "docs/00_project/REQUIREMENTS.md": """# Requirements

Este arquivo deve transformar os requisitos fornecidos pelo professor
em requisitos rastreáveis do projeto.

## Academic requirements

TODO: analisar o PDF oficial.

## Nexo requirements

TODO: definir requisitos funcionais.

## Traceability

Cada requisito deverá possuir:

- ID;
- descrição;
- origem;
- implementação;
- teste;
- status.
""",

    "docs/00_project/SCOPE.md": """# Scope

## MVP

TODO.

## Future features

TODO.

## Out of scope

TODO.
""",

    "docs/00_project/ROADMAP.md": """# Roadmap

## Phase 0 — Foundation

- [ ] requisitos
- [ ] escopo
- [ ] arquitetura
- [ ] ambiente
- [ ] identidade visual

## Phase 1 — Core domain

- [ ] ativos
- [ ] carteiras
- [ ] transações
- [ ] posições

## Phase 2 — Market data

- [ ] API externa
- [ ] cotações
- [ ] histórico
- [ ] cache

## Phase 3 — Analysis

- [ ] indicadores
- [ ] valuation
- [ ] preço teto
- [ ] projeções

## Phase 4 — User interface

- [ ] shell principal
- [ ] dashboard
- [ ] mercado
- [ ] carteira
- [ ] análises

## Phase 5 — Advanced features

- [ ] alertas
- [ ] planejamento financeiro
- [ ] educação financeira

## Phase 6 — Delivery

- [ ] testes
- [ ] documentação
- [ ] relatório
- [ ] apresentação
- [ ] demo
""",

    "docs/00_project/DELIVERY_CHECKLIST.md": """# Delivery Checklist

- [ ] Requisitos acadêmicos atendidos
- [ ] Aplicação executável
- [ ] Banco de dados funcionando
- [ ] API externa funcionando
- [ ] Testes executados
- [ ] README atualizado
- [ ] Manual de instalação
- [ ] Manual do usuário
- [ ] Relatório final
- [ ] Slides finais
- [ ] Demo preparada
""",

    "docs/00_project/DECISIONS.md": """# Project Decisions

Registro simplificado das principais decisões do projeto.

Decisões arquiteturais mais importantes devem receber um ADR próprio
em `docs/02_architecture/decisions/`.
""",

    "docs/01_professor/professor_notes.md": """# Professor Notes

Registrar aqui orientações fornecidas pelo professor em aula ou
fora dos documentos oficiais.
""",

    "docs/01_professor/requirement_traceability.md": """# Requirement Traceability

| Requirement | Source | Implementation | Test | Evidence | Status |
|---|---|---|---|---|---|
| TODO | TODO | TODO | TODO | TODO | TODO |
""",

    "docs/02_architecture/ARCHITECTURE.md": """# Nexo Architecture

## Initial architecture

```text
PySide6 UI
    |
    v
Application
    |
    v
Domain
   / \\
  v   v
Database / External APIs
Dependency rules

TODO: detalhar após análise dos requisitos acadêmicos.
""",

"docs/02_architecture/DOMAIN_MODEL.md": """# Domain Model

TODO: definir entidades e relacionamentos do domínio.
""",

"docs/02_architecture/DATABASE.md": """# Database Architecture

Initial proposal:

SQLite
SQLAlchemy ORM

TODO: definir schema.
""",

"docs/02_architecture/API_ARCHITECTURE.md": """# External API Architecture

TODO: definir provedores e interfaces para dados financeiros.
""",

"docs/02_architecture/UI_ARCHITECTURE.md": """# UI Architecture

PySide6 será utilizado para a interface desktop.

TODO: definir navegação, páginas, controllers e view models.
""",

"docs/03_design/DESIGN_SYSTEM.md": """# Nexo Design System
Brand

TODO.

Colors

TODO.

Typography

TODO.

Components

TODO.

Charts

TODO.

Navigation

TODO.

Themes

TODO.
""",

"docs/03_design/UI_GUIDELINES.md": """# UI Guidelines

TODO.
""",

"docs/03_design/USER_FLOWS.md": """# User Flows

TODO.
""",

"docs/04_development/DEVELOPMENT_GUIDE.md": """# Development Guide

TODO.
""",

"docs/04_development/ENVIRONMENT.md": """# Development Environment
Create environment
python -m venv .venv
Windows
.venv\\Scripts\\activate
Linux/macOS
source .venv/bin/activate
Install
pip install -r requirements.txt
pip install -r requirements-dev.txt
Tests
pytest
Lint
ruff check .

""",

"docs/04_development/CODING_STANDARDS.md": """# Coding Standards
utilizar type hints;
preferir classes pequenas com responsabilidade clara;
evitar código duplicado;
documentar decisões não triviais;
separar domínio, infraestrutura e UI;
criar testes para regras de negócio;
utilizar nomes explícitos;

evitar números mágicos.
""",

"docs/04_development/TESTING.md": """# Testing

Unit tests

Regras de negócio e cálculos.

Integration tests

Banco de dados e APIs externas.

UI tests

Interações importantes da interface.
""",

"docs/06_progress/CURRENT_STATUS.md": """# Current Project Status
Current phase

Phase 0 — Foundation

Completed
conceito inicial do projeto;
nome Nexo escolhido;
estrutura inicial do repositório.
In progress
análise dos requisitos do professor;
definição do MVP;
definição da arquitetura.
Next tasks
adicionar PDF oficial do projeto;
adicionar slides/material das aulas;
extrair requisitos acadêmicos;
definir MVP;
definir modelo de domínio;
validar arquitetura;

iniciar primeira vertical slice.
""",

"docs/06_progress/BACKLOG.md": """# Backlog

Foundation
 analisar requisitos do professor
 definir MVP
 definir arquitetura
 definir modelo de dados
 definir design system
Development

TODO.
""",

"src/nexo/__init__.py": "",
"src/nexo/main.py": """def main() -> None:
print("Nexo")

if name == "main":
main()
""",

"src/nexo/core/__init__.py": "",
"src/nexo/domain/__init__.py": "",
"src/nexo/application/__init__.py": "",
"src/nexo/infrastructure/__init__.py": "",
"src/nexo/calculations/__init__.py": "",
"src/nexo/ui/__init__.py": "",

"tests/conftest.py": "",

"data/README.md": """# Data

Arquivos locais de desenvolvimento.

Não armazenar credenciais ou dados sensíveis neste diretório.
""",

"deliverables/README.md": """# Deliverables

Arquivos finais destinados à entrega.

Os documentos-fonte devem permanecer em docs/.
""",
}

def create_directories() -> None:
    for directory in DIRECTORIES:
        path = ROOT / directory
        path.mkdir(parents=True, exist_ok=True)
        print(f"[DIR] {directory}")

def create_files() -> None:
    for filename, content in FILES.items():
        path = ROOT / filename
        path.parent.mkdir(parents=True, exist_ok=True)

        if path.exists():
            print(f"[SKIP]   {filename}")
            continue

        path.write_text(content, encoding="utf-8")
        print(f"[CREATE] {filename}")

def create_gitkeep_files() -> None:
    for directory in DIRECTORIES:
        path = ROOT / directory

        if not any(path.iterdir()):
            gitkeep = path / ".gitkeep"
            gitkeep.touch()
            print(f"[KEEP]   {directory}/.gitkeep")

def main() -> None:
    print("=" * 60)
    print("NEXO PROJECT BOOTSTRAP")
    print(f"Root: {ROOT}")
    print("=" * 60)

    print("\n[1/3] Creating directories...\n")
    create_directories()

    print("\n[2/3] Creating initial files...\n")
    create_files()

    print("\n[3/3] Adding .gitkeep to empty directories...\n")
    create_gitkeep_files()

    print("\n" + "=" * 60)
    print("Nexo project structure created successfully.")
    print("=" * 60)

if __name__ == "__main__":
    main()