# Ambiente de desenvolvimento

## Pré-requisitos

- Python >=3.10 compatível com as dependências;
- Windows para validação final da interface;
- incremento 01 validado com Python 3.14.0, PySide6/Qt 6.11.2 e SQLAlchemy 2.1.3.

## Preparação no Windows

Na raiz do clone:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m nexo.main
```

Usar o executável diretamente evita depender da política de ativação do
PowerShell. Opcionalmente, ative com `.venv\Scripts\Activate.ps1` e use
`python -m nexo.main`.

## Linux

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e .
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m nexo.main
```

Os comandos Linux são equivalentes; este incremento foi verificado no Windows.

## Dependências

`requirements.txt` é a fonte única de dependências de execução: PySide6,
SQLAlchemy >=2.0 e <3, httpx, pydantic e python-dotenv. O setuptools lê esse
arquivo em `pyproject.toml`, portanto `pip install -e .` também instala as
dependências. Algumas bibliotecas permanecem reservadas para etapas futuras.

`requirements-dev.txt` declara pytest, pytest-cov, pytest-qt, Ruff e mypy.

## Banco e configuração

`default_database_path()` resolve `data/nexo.db` a partir de `session.py` no
checkout instalado em modo editável, sem depender do current working directory.
A inicialização cria o diretório e as tabelas `portfolios`/`transactions`, sem apagar dados
existentes. Os testes usam bancos temporários próprios.

O `.env` é carregado opcionalmente para BRAPI_TOKEN/BRAPI_API_KEY e BRAPI_BATCH_SIZE.
Ambiente exportado tem prioridade; app inicia sem token. Configurações legadas
genéricas de banco, mercado e e-mail em `.env.example` permanecem exemplos para
configuração futura; não alteram o banco ou adapter. Nenhuma credencial é necessária
para iniciar e experimentar os tickers públicos. Não versione
`.env` nem bancos locais. A distribuição executável/wheel fora do checkout e
seu diretório de dados ainda não foram definidos.

## Verificações

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m compileall -q src tests bootstrap_project.py
.\.venv\Scripts\python.exe -m pip check
Remove-Item Env:QT_QPA_PLATFORM
```

Use `offscreen` para verificações automatizadas. A aparência em diferentes
escalas/monitores do Windows continua exigindo validação manual.
