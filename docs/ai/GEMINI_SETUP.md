# Configuração — basta incluir a chave

No executável Windows, o `.env` fica **ao lado de `Nexo.exe`**, fora de `_internal`.
O build não copia suas chaves do checkout. A tela inicial escolhe Demo/Normal;
os bancos ficam em `%LOCALAPPDATA%\NexoInvest`, separados dos arquivos em `data/`
do desenvolvimento. [Distribuição Windows](../04_development/WINDOWS_EXECUTABLE.md).

Projeto informado pelo usuário:

- Nome: NEXO Intelligence.
- Recurso/número: `projects/1029731024680` / `1029731024680`.
- ID: `gen-lang-client-0662974523`.

Esses dados já estão nos defaults e no `.env.example`. A autenticação é feita
pela chave Gemini vinculada ao projeto; não é necessário inserir o número em
requisições nem configurar Vertex AI/ADC. O Nexo não habilita serviços ou billing.

No Windows, na raiz `T:\nexo`:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
notepad .env
```

Inclua no arquivo existente, preservando suas configurações de mercado:

```dotenv
GEMINI_API_KEY=SUA_CHAVE_LOCAL
```

Não envie sua chave no chat nem a inclua em commits. O `.env` é ignorado pelo
Git. Não copie o `.env.example` por cima de um `.env` existente.

```powershell
.\.venv\Scripts\python.exe -m nexo.main
```

Abra **NEXO Intelligence**. O padrão `NEXO_AI_PROVIDER=auto` escolhe Gemini se
houver chave, e modo offline se não houver. Na aba Configuração, o teste de
conexão consulta metadados do modelo em worker, sem gerar texto. Antes de
Analisar com Gemini, marque a autorização de envio descrita na própria página.
Não há chamadas Gemini apenas por abrir a página.

No Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
# Edite .env e inclua GEMINI_API_KEY, preservando as entradas existentes.
.venv/bin/python -m nexo.main
```

Modelos e limites opcionais (defaults seguros já existem):

```dotenv
NEXO_AI_PROVIDER=auto
NEXO_AI_ENABLED=true
NEXO_AI_MODEL=gemini-3.5-flash-lite
NEXO_AI_EXTRACTION_MODEL=gemini-3.5-flash-lite
NEXO_AI_VIDEO_MODEL=gemini-3.5-flash-lite
NEXO_AI_RETRIEVAL_MODEL=gemini-3.5-flash-lite
NEXO_AI_MAX_INPUT_TOKENS=32000
NEXO_AI_MAX_OUTPUT_TOKENS=2048
NEXO_AI_DAILY_REQUEST_LIMIT=20
NEXO_AI_DAILY_TOKEN_LIMIT=200000
NEXO_AI_MAX_TOOL_CALLS=8
NEXO_AI_FILE_SEARCH_STORE=
YOUTUBE_API_KEY=
```

Ambiente prevalece sobre o arquivo, UTF-8/BOM aceito. Reinicie após alterar a
configuração. `mock` força modo offline mesmo com chave. `false` desativa o
agente. Não há editor/persistência de segredos na GUI.

O limite de entrada usa bytes UTF-8 como estimativa conservadora para texto,
incluindo instruções e schemas; saída é limitada pelo SDK. Uso retornado pelo
Google substitui a reserva de tokens; falhas sem metadata conservam a reserva.
Cotas locais reiniciam por data UTC e contam cada tentativa. São independentes
dos limites dos providers financeiros e das quotas oficiais do Google.

File Search é opcional: configure um store existente `fileSearchStores/...`.
Apenas a chave é necessária para conversar, consultar ferramentas e usar a
biblioteca textual local. A chave YouTube é separada e só necessária ao catálogo.

Diagnóstico: 401/403 indicam chave/permissão/modelo; 429 aplica uma retentativa
com backoff curto e depois interrompe. Falha de síntese Gemini exibe erro e permite
tentar novamente; não substitui a interpretação por resposta local. Sem estimativas permitidas, o valuation fica
indisponível e os dados consultados são preservados. Verifique o modelo no AI Studio se seu projeto não tiver
acesso ao default. Não há fallback silencioso para um modelo mais caro.
Configuração inválida de limites/store desativa somente a IA com mensagem
segura; o restante do Nexo continua disponível.

## Uso da Missão 2

No Copiloto, abra Contexto e selecione a carteira. Pergunte "Analise toda a minha
carteira e identifique as melhores oportunidades nas condições atuais".
A intenção aciona investigação; também há opção explícita no contexto.
Permitir estimativas produz cenários ilustrativos; desligue para análise só de
dados observados. A autorização de envio é necessária ao Gemini, inclusive à
proposta de hipóteses. Para trabalhar sem envio ao Gemini, configure
`NEXO_AI_PROVIDER=mock` e reinicie; esse modo produz o relatório local.

Consulte Relatório financeiro para cenários, fontes, datas, histórico e exposição.
Enter envia; Shift+Enter quebra linha. Exportar análise salva Markdown humano;
detalhes técnicos e diagnóstico JSON ficam sob ação explícita. Follow-ups como
"Refaça com margem de segurança de 25%" mantêm o contexto selecionado.
File Search é administrado pela CLI: [KNOWLEDGE_PIPELINE](KNOWLEDGE_PIPELINE.md).
Os 15 documentos locais dispensam File Search. O wheel inclui a biblioteca;
no checkout sua fonte é `docs/ai/knowledge`.
