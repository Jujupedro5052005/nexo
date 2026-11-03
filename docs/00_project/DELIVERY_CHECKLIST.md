# Checklist da entrega final

Orientações informadas em 03/11/2026: apresentação de **8–12 minutos**, prints
selecionados/comentados, pasta completa do projeto e planilha de avaliação.
Este checklist não substitui a planilha oficial do professor.

## Preparação do conteúdo

- [ ] Ensaiar o [roteiro de dez minutos](../04_development/FINAL_PRESENTATION.md).
- [ ] Demonstrar um fluxo completo com persistência após reabrir.
- [ ] Selecionar prints atuais dos gráficos e dos métodos de POO indicados no roteiro.
- [ ] Distinguir preços fictícios, dados reais de API e respostas locais/Gemini.
- [ ] Explicar limites de IR, TWR aproximado e alertas manuais.
- [ ] Comparar a proposta com a implementação real, inclusive Portfolio sem posições internas.

## Pasta e arquivos a entregar

- [ ] **Código completo:** `src/`, `scripts/`, `tests/`, `docs/`, `deliverables/`,
  `launcher.py`, `Nexo.spec`, `pyproject.toml`, `pytest.ini`, arquivos requirements,
  README e `.env.example`; manter a estrutura das pastas.
- [ ] **Executável:** ZIP com `Nexo.exe` e `_internal`, instruções e template de configuração;
  o ZIP de executável complementa o código, não substitui a pasta do projeto.
- [ ] **Planilha oficial de avaliação:** obter o modelo do professor, preencher os
  campos solicitados e anexar. Não localizada no repositório/anexos nesta revisão.
- [ ] Incluir a versão final dos slides e a proposta revisada; manter cópia de segurança.
- [ ] Excluir `.env` e variantes privadas, bancos pessoais/IA, sidecars SQLite,
  caches, logs, `.venv`, `.git` e arquivos temporários.
- [ ] Conferir o conteúdo do ZIP e identificar o commit usado para gerar o executável.

Para exportar **os arquivos versionados do commit aprovado**, na raiz do
repositório, com Git instalado:

```powershell
New-Item -ItemType Directory -Force dist
git archive --format=zip --prefix=Nexo-Projeto/ --output=dist/Nexo-Projeto.zip HEAD
git rev-parse HEAD
```

Execute após o merge e atualização local da `master`, ou no commit aprovado do
PR. `git archive` não inclui alterações não commitadas nem arquivos ignorados;
confira os arquivos versionados antes. Acrescente slides e planilha oficial à
pasta final separadamente caso não estejam no commit. Não adicione credenciais
para tornar a entrega executável: Apresentação não precisa delas.

## Aceite na máquina de apresentação

- [ ] Instalar pelo README em ambiente novo ou extrair o executável completo.
- [ ] Abrir no Windows alvo, idealmente sem Python; conferir resolução e escala.
- [ ] Abrir Apresentação sem internet; conferir caixa, patrimônio e gráficos preenchidos.
- [ ] Criar carteira e registrar compra/venda; rejeitar saldo insuficiente.
- [ ] Fechar/reabrir e conferir persistência e separação de Meu ambiente.
- [ ] Exportar CSV e conferir os valores no aplicativo de planilhas utilizado.
- [ ] Se mostrar API real, testar uma consulta pequena antes da aula e preparar
  captura datada como contingência; não atribuir um teste com mocks à API real.
- [ ] Guardar um ZIP final congelado e anotar versão/commit; evitar mudanças após o ensaio.

Resultados desta revisão e pendências: [FINAL_REVIEW.md](FINAL_REVIEW.md).
