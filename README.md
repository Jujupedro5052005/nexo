# Nexo Invest

Aplicação desktop de investimentos simulados e planejamento financeiro, desenvolvida para a disciplina de Programação Orientada a Objetos. Python, PySide6, SQLAlchemy e SQLite. Não executa ordens reais.

## Rodar o código

No Windows, com Python 3.10 ou superior instalado:

```powershell
git clone --branch master https://github.com/Jujupedro5052005/nexo.git
cd nexo
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe launcher.py
```

O launcher resolve o pacote `src/nexo` diretamente. Para desenvolvimento com `python -m nexo.main`, instale também com `python -m pip install -e .` dentro do ambiente virtual.

Na entrada, escolha **Apresentação** ou **Meu ambiente**. Os atalhos `python launcher.py --demo` e `--normal` continuam disponíveis.

## O que explorar

- **Apresentação:** três carteiras (Longo Prazo, Dividendos e Crescimento), 93 compras/vendas e 21 posições. Caixa aberto, aporte, retirada, dividendos, JCP, taxas e imposto em cada carteira. Orçamento mensal, três metas e três alertas editáveis.
- Preços, históricos e fundamentos de exemplo disponíveis sem internet para os 16 símbolos do catálogo. Fontes identificam os dados fictícios. ETFs não recebem fundamentos corporativos artificiais. Não são preços atuais de bolsa.
- Visão Geral: caixa, patrimônio, posições, ganhos/perdas e concentração. Movimentações: histórico e eventos financeiros. Análises: valuation, cenários e desempenho. Planejamento: orçamento, projeções e alocação. Relatórios: CSV e apoio parcial de IR.
- **NEXO Intelligence:** chat com copiloto visual, contexto da carteira e relatórios. Uma pergunta sobre PETR4 mantém PETR4 como foco; análise de toda a carteira depende de pedido explícito.
- **Meu ambiente:** começa sem exemplos e utiliza os provedores de mercado configurados. Ausência de dados reais aparece como indisponibilidade, sem substituição por preços de apresentação.

## Gemini e mercado

Opcionalmente copie `.env.example` para `.env` e preencha suas próprias chaves. Gemini usa `GEMINI_API_KEY`, seleção automática do provedor e autorização de envio do contexto na interface. Reinicie após editar o arquivo. Nenhuma credencial acompanha o projeto.

Sem chave, a análise local continua disponível, com identificação do provedor. Erros do Gemini são apresentados; não são silenciosamente convertidos em uma resposta local. Gemini exige internet e pode gerar cobrança na conta configurada.

[Configuração Gemini](docs/ai/GEMINI_SETUP.md) · [Integração de mercado](docs/02_architecture/BRAPI_CONFIGURATION.md)

## Persistência e entrega ao professor

No código, os dados ficam em `data/`. No executável, em `%LOCALAPPDATA%\NexoInvest`. Apresentação usa `nexo_demo.db`; o ambiente pessoal usa `nexo.db`. O histórico da IA tem banco separado. Alterações persistem ao fechar e reabrir; os exemplos são importados uma vez. Atualizar a pasta do executável não substitui esses bancos.

Para testar sem instalar Python, extraia o ZIP completo e abra `Nexo.exe`, mantendo `_internal` ao lado dele. Envie a pasta inteira, incluindo `LEIA-ME.txt` e `.env.example`; não envie `.env` nem seus bancos. O pacote é para Windows da mesma arquitetura usada no build. Gemini autenticado exige configuração própria do professor.

[Distribuição Windows](docs/04_development/WINDOWS_EXECUTABLE.md) · [Pendências reais](TODO.md)

## Arquitetura e avaliação

UI → Application → Domain/Calculations; Infrastructure implementa persistência e provedores. Transações e eventos financeiros são persistidos; posições e caixa são reconstruídos. A interface não consulta SQLite nem HTTP diretamente. Valores financeiros usam `Decimal`.

[Visão do projeto](docs/00_project/PROJECT_OVERVIEW.md) · [Requisitos](docs/00_project/REQUIREMENTS.md) · [Arquitetura](docs/02_architecture/ARCHITECTURE.md) · [Estado atual](docs/06_progress/CURRENT_STATUS.md)

Para desenvolvimento, instale `requirements-dev.txt`. Testes direcionados da entrega:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/integration/test_professor_delivery.py tests/ui/test_professor_delivery.py tests/ui/test_main_window.py tests/intelligence/test_hotfix_focus.py
```
