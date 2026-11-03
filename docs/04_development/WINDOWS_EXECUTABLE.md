# Executável Windows e apresentação

## Abrir o aplicativo

Na distribuição em pasta, abra `Nexo\Nexo.exe`. Mantenha a pasta `_internal` ao
lado do executável. A tela inicial oferece Apresentação e Meu ambiente, sem terminal ou flags.
Fechar essa tela cancela a abertura. Em desenvolvimento, use `python -m nexo.main`.
`--demo` e `--normal` continuam disponíveis como atalhos opcionais.

Normal preserva registros anteriores. Demo usa `nexo_demo.db` e importa exemplos
complementares uma vez, sem duplicação. No executável, bancos e caches ficam em
`%LOCALAPPDATA%\NexoInvest`; no checkout, continuam em `data/`. A versão empacotada
não importa automaticamente bancos do checkout. Feche o aplicativo antes de
copiar um backup; nunca substitua um banco com a aplicação em execução.

Para Gemini/mercado, edite um `.env` externo ao lado de `Nexo.exe`, preservando
entradas existentes. Inclua sua própria chave, sem enviá-la ao repositório.
O build não copia o `.env` do desenvolvimento. Variáveis de ambiente continuam
prevalecendo. A biblioteca de 15 capítulos já está incluída; File Search é opcional.

Hotfix: se não existir `.env` ao lado do EXE, também é aceito o `.env` do diretório
de onde ele foi executado. Assim, iniciar `dist\Nexo\Nexo.exe` pela raiz do checkout
usa sua configuração existente. No duplo clique, mantenha o arquivo ao lado do EXE.

## Gerar a distribuição

No PowerShell, na raiz do checkout:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm Nexo.spec
.\.venv\Scripts\python.exe scripts/package_windows.py
```

Resultado: `dist\Nexo\Nexo.exe`. Distribua a pasta inteira; enviar somente o EXE
não inclui Python, DLLs Qt ou biblioteca. O build em pasta facilita inspeção e
diagnóstico, e mantém dados graváveis fora do bundle. `Nexo.spec` não inclui
credenciais, bancos ou caches. Use o mesmo Windows/arquitetura alvo; a receita
não é compilação cruzada para Linux/macOS. Não há assinatura de código nesta etapa.

O terceiro comando gera `dist\Nexo-Windows.zip`, com a pasta inteira, instruções
e template sem valores de chaves/tokens. Recusa `.env`, bancos e contador de
consumo dentro da distribuição. Não inclua seus próprios dados ao enviar o ZIP.

As dependências de build ficam separadas das dependências de execução.
Referências: [PyInstaller spec files](https://pyinstaller.org/en/stable/spec-files.html)
e [recursos em runtime](https://pyinstaller.org/en/stable/runtime-information.html).

## Validar sem usar seus bancos ou consumir APIs

```powershell
.\.venv\Scripts\python.exe scripts/smoke_executable.py dist/Nexo/Nexo.exe --capture tmp/executable-startup.png
.\.venv\Scripts\python.exe scripts/smoke_executable.py dist/Nexo/Nexo.exe --mode normal --capture tmp/executable-normal.png
.\.venv\Scripts\python.exe scripts/smoke_executable.py dist/Nexo/Nexo.exe --mode demo --capture tmp/executable-demo.png
```

O smoke abre janelas reais, verifica o PID criado e fecha apenas essas janelas.
Usa diretório temporário, modo mock de IA e budgets financeiros zero. A entrada
é validada sem flags de produto; os dois outros smokes validam os atalhos e a
composição congelada. Ao sair, confere isolamento dos bancos, corpus e exemplos.
Isso não substitui teste de toda a aplicação em um Windows sem Python instalado.

Evite rodar smokes em paralelo à apresentação. Eles criam suas próprias janelas
e não encerram uma instância do usuário.

## Mercado online nos dois modos

Apresentação e Meu ambiente usam os mesmos provedores online para cotações,
históricos, fundamentos e proventos. Sem dados reais disponíveis, os indicadores
correspondentes ficam indisponíveis. Não há provedor fictício na aplicação.
Caixa, transações e planejamento permanecem locais. Gemini exige chave e autorização.

Entrega atual: `dist/Nexo-Professor.zip`, gerada em `dist/Online/Nexo` para não
sobrescrever executáveis antigos em uso. Envie o ZIP completo. O professor extrai
a pasta Nexo e abre Nexo.exe; não precisa instalar Python. Alterações ficam no
perfil dele e sobrevivem à reabertura e à atualização da pasta do programa.
Não foi realizado aceite em outra máquina sem Python.

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --distpath dist/Online Nexo.spec
.\.venv\Scripts\python.exe scripts/package_windows.py --folder dist/Online/Nexo --destination dist/Nexo-Professor.zip
```

Roteiro e capturas: [relatório final](../ai/FINAL_IMPLEMENTATION_REPORT.md).
