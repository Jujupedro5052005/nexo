# Nexo Invest

**Simulador e Plataforma de Análise de Investimentos**, desenvolvido para a
disciplina de Programação Orientada a Objetos.

Aplicação desktop educacional e de simulação. Não executa ordens reais,
não mantém custódia e não oferece recomendação personalizada.

## Status

**Grande Incremento 04: mercado real, valuation e dashboard.**
Crie/selecione uma carteira, registre BUY/SELL simulados, consulte o ledger e
posições, e reencontre as operações após reabrir o aplicativo. Carteiras e Visão
Geral exibem custo, realizado e contagens locais; cotações disponíveis da brapi
adicionam valor das posições abertas, não realizado, resultado total e retorno
sobre o custo aberto. O dashboard inclui gráfico real de custo versus valor.

Em Ativos, busque código/nome (ex.: PETR), selecione PETR4 e consulte cotação,
moeda, variação e histórico diário de 1 mês, 3 meses ou 1 ano. O gráfico usa
fechamentos da API; período, fonte e horários ficam identificados.

Sem internet/token válido, o ledger continua funcionando. Métricas de mercado
indisponíveis mostram “—”, nunca um preço demo. Sem token, os símbolos públicos
PETR4, VALE3, ITUB4 e MGLU3 permitem experimentar a integração; busca do catálogo
não exige autenticação. Acesso/períodos/limites dependem do plano e da API.

Evolução patrimonial histórica, alocação por categoria, benchmarks, insights,
fluxo de caixa, metas, alertas, planejamento e análises complementares permanecem
demo, rotulados por seção. Mercado das posições abertas não é patrimônio total:
caixa/aportes/retiradas ainda não são modelados. Edição/exclusão e comparação
continuam pendentes. Não há persistência de quotes, posições ou valuation.

Entradas numéricas aceitam `10`, `10,50`, `10.50`, `0,25`, `0.25` e `1.234,56`.
Um ponto isolado é decimal: `1.234` representa 1,234. Agrupamento brasileiro
exige vírgula decimal. Quantidade/preço são positivos; taxas podem ser zero.
Não use prefixo R$, sinais ou notação exponencial no formulário. Datas da UI
são horários sem fuso; o armazenamento não lhes atribui timezone.

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
UI -> Application -> Domain + contratos de repositories / MarketDataProvider
                                  ^
                 Implementações SQLAlchemy -> SQLite (portfolios + transactions)

MarketDataProvider <- BrapiMarketDataProvider -> httpx -> brapi v2
Application -> Calculations (valuation Decimal)
main.py compõe as dependências.
```

O fluxo usa Python, PySide6, SQLite, SQLAlchemy e httpx. HTTP fica exclusivamente
na Infrastructure; workers Qt executam casos de uso fora da thread de interface.

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
checkout, independentemente da pasta de onde a aplicação é iniciada.

## Configuração de mercado

O app carrega opcionalmente `.env` da raiz do checkout, preservando variáveis já
exportadas pelo ambiente. Copie `.env.example` para `.env` e preencha apenas se
precisar de acesso autenticado:

```dotenv
BRAPI_TOKEN=
BRAPI_BATCH_SIZE=5
```

`BRAPI_API_KEY` também é aceito, com prioridade para `BRAPI_TOKEN`. O token viaja
somente no header Bearer; não copie credenciais para código, testes ou logs.
`.env` e variantes são ignorados pelo Git, exceto `.env.example`. As variáveis
legadas genéricas MARKET_API_KEY/BASE_URL não configuram este adapter.
O timeout é explícito de 10 segundos por operação de rede; não há polling ou
retry automático. “Atualizar mercado” força consulta nova; “Atualizar ativo”
atualiza cotação/histórico. Sem cache de provider ou tabela de preços; somente
a última fotografia da tela é reutilizada enquanto o contexto não muda.

[Integração, endpoints, fórmulas e restrições](docs/02_architecture/API_ARCHITECTURE.md).

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
