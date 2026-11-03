# Validação de NEXO Intelligence

Na raiz do projeto, Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest tests/intelligence -q
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m compileall -q src tests
git diff --check
```

Linux: use `.venv/bin/python`; Qt sem display pode exigir `QT_QPA_PLATFORM=offscreen`.
Os testes comuns bloqueiam sockets reais e usam bancos temporários, fixtures,
`MockTransport` ou clientes controlados. Não leem chaves reais para gerar respostas.

Cobertura: resultados conhecidos Gordon/yield/múltiplos; NaN/Infinity, Ke ≤ g,
classes incompatíveis, zero explícito, dados ausentes, sensitividade; schemas
de ferramentas e serialização HTTP pelo SDK real; erros 401/403/429/500,
backoff, parsing inválido, cotas concorrentes/reabertura; autorização/dedup,
File Search assíncrono/indexação única/exclusão; aprovação/versionamento;
canal incorreto, metadados/expiração, vídeo autorizado; história local;
conteúdo malicioso tratado como dado; worker Qt responsivo e resposta cancelada.

Os testes reais são **desativados por padrão**. Para autorizar somente o smoke de
metadados, com chave já configurada:

```powershell
$env:NEXO_AI_LIVE_TEST='1'
.\.venv\Scripts\python.exe -m pytest tests/intelligence/test_live_gemini.py::test_live_model_metadata -q
```

Geração real exige outra autorização explícita e pode consumir quota/custo:

```powershell
$env:NEXO_AI_ALLOW_LIVE_GENERATION='1'
.\.venv\Scripts\python.exe -m pytest tests/intelligence/test_live_gemini.py::test_live_single_authorized_generation -q
Remove-Item Env:NEXO_AI_LIVE_TEST
Remove-Item Env:NEXO_AI_ALLOW_LIVE_GENERATION
```

No Linux, prefixe os comandos com as variáveis, como
`NEXO_AI_LIVE_TEST=1 .venv/bin/python -m pytest ...`. A geração autorizada usa uma
única chamada, limite local de uma requisição e até 128 tokens de saída; o banco
de uso do teste é temporário. Esses smokes não validam File Search, direitos de
conteúdo, vídeo ou quota real completa. Não execute ambos em loops.

Resultados finais e diferenças entre mocks e integrações externas:
[IMPLEMENTATION_REPORT.md](IMPLEMENTATION_REPORT.md).

Registro de 03/11/2026: suíte completa 764 aprovados/2 ignorados (376,84 s);
regressão final após ajustes de UI/precisão: 77 testes de IA aprovados/2 ignorados
(5,75 s). Verificações Ruff, mypy (146 arquivos), compileall e diff-check verdes.
