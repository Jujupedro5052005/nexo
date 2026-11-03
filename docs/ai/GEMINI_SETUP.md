# Configuração — basta incluir a chave

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
com backoff curto e depois interrompe. Falha de síntese não salva turno parcial.
Ausência de premissas gera resultado financeiro indisponível, preservando os
dados consultados. Verifique o modelo no AI Studio se seu projeto não tiver
acesso ao default. Não há fallback silencioso para um modelo mais caro.
Configuração inválida de limites/store desativa somente a IA com mensagem
segura; o restante do Nexo continua disponível.
