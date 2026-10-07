# Nexo Invest

**Simulador e Plataforma de Análise de Investimentos**, desenvolvido para a
disciplina de Programação Orientada a Objetos.

Aplicação desktop educacional e de simulação. Não executa ordens reais,
não mantém custódia e não oferece recomendação personalizada.

## Status

**Grande Incremento 05.2: multi-provider, snapshot avançado e controle de consumo.**
Crie/selecione uma carteira, registre BUY/SELL simulados, consulte o ledger e
posições, e reencontre as operações após reabrir o aplicativo. Carteiras e Visão
Geral exibem custo, realizado e contagens locais; cotações disponíveis da brapi
adicionam valor das posições abertas, não realizado, resultado total e retorno
sobre o custo aberto. O dashboard inclui gráfico real de custo versus valor.

Em Ativos, busque código/nome (ex.: PETR), selecione PETR4 e consulte cotação,
moeda, variação e histórico diário de 1 mês, 3 meses ou 1 ano. O gráfico usa
fechamentos da API; período, fonte e horários ficam identificados. Ativos também
consulta fundamentos e dez indicadores. A página Análises permite informar ticker,
período e yield requerido (%) explícito para Bazin; Graham exige LPA/VPA positivos.
Preços calculados, margem de segurança e risco do histórico têm premissas e origem.
Sem yield informado, fundamentos e Graham continuam disponíveis.

Em Análises → Carteiras / comparação, selecione duas ou mais carteiras por ID,
inclusive com nomes iguais. Compare custo, valor aberto, realizado, não realizado,
total, retorno aberto, pesos, maior posição, top 3 e HHI. Carteiras/Visão Geral
também mostram concentração real quando o valuation BRL está completo.

Sem internet/token válido, o ledger continua funcionando. Métricas de mercado
indisponíveis mostram “—”, nunca um preço demo. Sem token, os símbolos públicos
PETR4, VALE3, ITUB4 e MGLU3 permitem experimentar a integração; busca do catálogo
não exige autenticação. Acesso/períodos/limites dependem do plano e da API.

Evolução patrimonial histórica, benchmarks, insights, fluxo de caixa, metas,
alertas e planejamento permanecem demonstrativos, rotulados por seção. A alocação
demo por categoria foi removida da Visão Geral; concentração por ativo é real.
Mercado das posições abertas não é patrimônio total: caixa/aportes/retiradas ainda
não são modelados. TWR, XIRR/MWR e Sharpe ficam indisponíveis. Proventos externos
servem às análises do ativo, sem crédito no ledger. Edição/exclusão continua futura.
Não há persistência de quotes, fundamentos, posições ou valuation.

Entradas numéricas aceitam `10`, `10,50`, `10.50`, `0,25`, `0.25` e `1.234,56`.
Um ponto isolado é decimal: `1.234` representa 1,234. Agrupamento brasileiro
exige vírgula decimal. Quantidade/preço são positivos; taxas podem ser zero.
Não use prefixo R$, sinais ou notação exponencial no formulário. Datas da UI
são horários sem fuso; o armazenamento não lhes atribui timezone.

## Demonstração acadêmica

Com o ambiente virtual ativado, na raiz do projeto:

```powershell
python scripts/create_demo_dataset.py
python -m nexo.main --demo
```

O seed recria apenas `data/nexo_demo.db`, sem chamadas externas: três carteiras,
93 movimentações, 21 posições e 30 meses de histórico fictício. A primeira
abertura com `--demo` cria o banco se necessário; reaberturas preservam as
movimentações feitas durante a apresentação. Feche o app antes de resetar.
`data/nexo.db` e o modo normal permanecem separados. Cotações e análises usam
os providers reais e seus limites, sem preços inventados como fallback.

Roteiro, cobertura dos gráficos e limitações:
[DEMO_PRESENTATION.md](docs/04_development/DEMO_PRESENTATION.md).

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

MarketDataProvider + FundamentalDataProvider <- Cache <- BrapiMarketDataProvider -> httpx -> brapi v2
Application -> Calculations (indicadores, valuation, risco e concentração Decimal)
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

### Sandbox público

Sem chave, PETR4, MGLU3, VALE3 e ITUB4 podem ser consultados. A busca pode encontrar
ITSA3, mas consultar seus detalhes exige autenticação. Ativos explica a limitação
e oferece “Configurar integração”, que abre Configurações.

### Uso autenticado no Windows

Crie `.env` na raiz do checkout (use `.env.example` como referência). Crie/copie sua
chave em [brapi dashboard](https://brapi.dev/dashboard) e preencha:

```dotenv
BRAPI_TOKEN=SUA_CHAVE
BRAPI_BATCH_SIZE=1
```

Depois inicie ou reinicie o aplicativo:

```powershell
.\.venv\Scripts\python.exe -m nexo.main
```

`python-dotenv` já carrega `.env` automaticamente, independentemente do diretório
atual; não é necessário exportar `$env:` a cada terminal. Leitura UTF-8/BOM é aceita.

Precedência: cada variável existente no ambiente prevalece sobre a mesma variável
do arquivo (`override=False`). Depois, `BRAPI_TOKEN` não vazio prevalece sobre
`BRAPI_API_KEY` não vazio; valores em branco são ausentes. Portanto, TOKEN no arquivo
vence API_KEY no ambiente quando TOKEN não está definido no ambiente. Uma variável
explicitamente vazia no ambiente impede a substituição pelo mesmo nome no arquivo.

Alternativa temporária para a sessão PowerShell:

```powershell
$env:BRAPI_TOKEN = "SUA_CHAVE"
.\.venv\Scripts\python.exe -m nexo.main
Remove-Item Env:BRAPI_TOKEN
```

O token viaja somente no header Bearer. Não é exibido nem salvo em SQLite.
`.env` e variantes são ignorados pelo Git, exceto `.env.example`. As variáveis
legadas `MARKET_API_KEY`/`MARKET_API_BASE_URL` não configuram este adapter; substitua
sua utilização por `BRAPI_TOKEN` no arquivo local.

Configurações mostra provider, chave configurada, modo e estado de autenticação.
“Testar conexão” consulta PETR4 por worker, sempre com uma requisição nova e com a
chave quando presente. Sucesso público não confirma acesso a ITSA3/plano; chave
presente não é sinônimo de autenticação comprovada. 401, 403, 429 e conexão têm
mensagens distintas. Depois de editar `.env`, reinicie o Nexo.

[Detalhes da configuração e diagnóstico](docs/02_architecture/BRAPI_CONFIGURATION.md).

O timeout é explícito de 10 segundos por operação de rede; não há polling ou
retry automático. Cache compartilhado em memória: cotações 30s, histórico 300s,
fundamentos/proventos 300s; no máximo 256 entradas, sem persistência. Chamadas
simultâneas para a mesma chave são compartilhadas. “Atualizar mercado”, “Atualizar
ativo”, “Atualizar dados” e “Atualizar comparação” invalidam o cache correspondente;
“Calcular” reutiliza dados válidos. A consulta preserva os timestamps originais.

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
- [status](docs/06_progress/CURRENT_STATUS.md) e [backlog](docs/06_progress/BACKLOG.md);
- [análises: fórmulas, fontes e premissas](docs/02_architecture/ANALYTICS.md).

## Providers — Grande Incremento 05.2

A composição real usa brapi para mercado, bolsai para fundamentos e metadados,
Yahoo/yfinance para proventos, splits e histórico longo, e CVM Dados Abertos
para cadastro/DFP/ITR. Ativos apresenta snapshot avançado e JSON normalizado
recolhível. EOD bolsai é fechamento diário; latência não significa tempo real.

Configuração sem credenciais reais (copie `.env.example` para seu `.env` local):

```env
BRAPI_TOKEN=
BRAPI_BATCH_SIZE=1
BOLSAI_API_KEY=
NEXO_PROVIDER_TEST_MODE=true
NEXO_BRAPI_SOFT_DAILY_BUDGET=100
NEXO_BOLSAI_SOFT_DAILY_BUDGET=40
NEXO_YAHOO_SOFT_DAILY_BUDGET=50
NEXO_CVM_SOFT_DAILY_BUDGET=2
```

brapi dividends e bolsai corporate-events só são habilitados por configuração
externa com acesso confirmado. Sem chave bolsai e sem bridge cacheado, a identidade
oficial é indisponível; não se tenta adivinhar a companhia. Yahoo não distingue
JCP nem fornece pagamento nessa consulta; Bazin exibe essas limitações.

Cache/coalescing são compartilhados pelas telas. Os budgets são locais, distintos
das quotas oficiais; não há polling. Datasets e usage JSON ficam em `data/`,
ignorados no Git. `pytest` bloqueia rede real por transportes e sockets.

Smoke online separado, com aviso anterior às consultas:

```powershell
python scripts/smoke_providers.py
python scripts/preview_snapshot.py
```

Máximo por execução: brapi 2 requests, bolsai 2 requests, Yahoo 1 operação de
ticker; CVM só lê cache válido. Não roda no pytest. Snapshot/captura sanitizados
ficam em `tmp/`. A captura nativa Windows exige fonts/plataforma Qt disponíveis.
Políticas completas: [DATA_PROVIDERS.md](docs/02_architecture/DATA_PROVIDERS.md).
