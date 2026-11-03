# Validação da missão final — 03/11/2026

| Verificação | Resultado executado |
|---|---|
| Baseline anterior às mudanças | 800 aprovados, 2 ignorados; 415,38 s |
| Suíte completa após ajustes | **820 aprovados, 2 ignorados; 436,26 s** |
| Regressão após indicador fixo de DEMO | **28 aprovados; 39,92 s** |
| Ruff | Aprovado |
| mypy | Aprovado em 160 arquivos de código |
| compileall | Aprovado em src, tests, scripts e launcher |
| diff-check | Aprovado |
| PyInstaller Windows x64 | Build em pasta concluído, sem console |
| Smokes nativos | Seletor, Normal e Demo abertos/fechados em processos próprios |
| ZIP de distribuição | 1.642 arquivos, 100.466.873 bytes; corpus incluído, sem `.env` ou bancos |

Artefato local: `dist/Nexo-Windows.zip`. SHA-256 da distribuição desta entrega:
`08412dd252629f0c2bd8ce23af5155f3db05ab0fc550741388a2b6ace402ba80`.
Binários gerados ficam fora do Git; a receita e os scripts estão versionados.

Os dois testes ignorados são smokes Gemini autenticados, desativados por padrão.
Um aviso de depreciação do SDK Google/Python permanece, sem falha associada.
Uma execução intermediária encontrou três expectativas antigas: ordem dos últimos
itens da navegação e simulação do caminho de configuração. Os testes foram
atualizados para a nova ordem e para `environment_file`, preservando as verificações
de destino correto, isolamento e precedência do ambiente. A suíte seguinte passou.

## O que foi exercitado

- Escolha visual, sem `--demo`, nos dois modos e nas duas dimensões de janela.
- Cancelamento antes da composição, sem criar banco/provider.
- Seed somente no DEMO, idempotência e preservação de registros.
- Planejamento preenchido, projeção e alocação com soma de 100%; metas/progresso
  e alertas com estado inicial explícito.
- Último item Configurações e atalhos que levam à página correta.
- Personagem em estados distintos, animação apenas durante análise visível e
  interrupção ao esconder/desativar movimento.
- Contexto redimensionável, nova conversa, pergunta limpa e relatório guiado.
- TWR com preparação de caixa, resumo de fluxos e distinção entre zero e ausência.
- Temas educacionais e encaminhamento ao Copiloto sem envio automático.
- Cálculo fiscal manual, valores inválidos/extremos, histórico anterior ao ano,
  splits registrados e exportação CSV exata.
- Caminhos congelados para corpus e `.env` externo, sem incorporar segredos.

## Capturas e executável

As capturas Qt dos testes usam fixtures explícitas, bancos temporários e providers
controlados em 1440×900 e 1180×720. O modo Demo do produto usa ledger fictício,
mas preços de mercado continuam dependentes dos providers; as fixtures de cotação
não são distribuídas como fallback.

Smokes nativos do EXE:

- [Seletor](screenshots/final/compiled-selector.png): abriu sem flags e cancelou
  sem criar bancos.
- [Normal](screenshots/final/compiled-normal.png): banco normal temporário, sem
  banco Demo e com 15 documentos canônicos carregados.
- [Demo](screenshots/final/compiled-demo.png): banco Demo temporário, sem banco
  Normal, corpus carregado e três metas persistidas.

O script limita sua ação ao PID que iniciou. Usa IA mock, budgets financeiros
zero e diretórios temporários. A checagem de SQLite fecha suas conexões antes da
limpeza. Não acessa os bancos originais nem encerra uma instância do usuário.

O bundle não foi avaliado numa máquina Windows sem Python instalado. Não é
assinado e não houve auditoria completa de drivers, DPI ou leitores de tela.
Inferência Gemini, File Search e processamento de vídeo não foram executados.
Nenhum custo de IA foi autorizado/iniciado para validar esta missão.

## Reproduzir

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m compileall -q src tests scripts launcher.py
git diff --check
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm Nexo.spec
```

O diretório das capturas dos novos testes é configurável por
`NEXO_FINAL_REVIEW_DIR`. Instruções dos três smokes e distribuição:
[WINDOWS_EXECUTABLE](../04_development/WINDOWS_EXECUTABLE.md).

[Relatório funcional e limites](FINAL_IMPLEMENTATION_REPORT.md).
