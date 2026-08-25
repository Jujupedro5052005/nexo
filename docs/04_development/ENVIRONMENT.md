# Ambiente de desenvolvimento

## Pré-requisitos

- Python 3.x compatível com as dependências;
- Windows para validação final da interface PySide6.

## Preparação

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

Em Linux/macOS, a ativação equivalente é `source .venv/bin/activate`, embora a
entrega da GUI deva ser validada no Windows.

## Dependências declaradas

`requirements.txt`: PySide6, SQLAlchemy, httpx, pydantic e python-dotenv.

`requirements-dev.txt`: pytest, pytest-cov, pytest-qt, ruff e mypy.

## Configuração

Copie `.env.example` para um `.env` local não versionado e preencha somente os
serviços em uso. As variáveis atualmente declaradas são:

- `NEXO_DATABASE_URL` (padrão de exemplo `sqlite:///data/nexo.db`);
- `MARKET_API_KEY` e `MARKET_API_BASE_URL`;
- `EMAIL_ADDRESS` e `EMAIL_APP_PASSWORD`.

As variáveis de mercado e e-mail podem permanecer vazias enquanto suas
integrações não forem implementadas. Nunca registre segredos no repositório.

## Verificações

```powershell
pytest
ruff check .
mypy src
```

A aplicação ainda não possui fluxo funcional; publique comando de execução
somente quando `main.py` realmente iniciar a interface.
