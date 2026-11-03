# Hotfix NEXO Intelligence — 03/11/2026

- Reproduzidos os dois casos reportados antes da correção.
- No executável, faltava `.env` ao lado do EXE e a chave da raiz era ignorada.
  Agora: ambiente do processo > `.env` ao lado do EXE > `.env` do diretório de
  execução quando o arquivo externo não existir. Nenhuma chave é distribuída.
- “Comprar/vender” não acionava análise de ativo; o modo aprofundado da UI podia
  sobrepor o foco e expandir a carteira. Ticker explícito agora fixa os ativos;
  carteira completa exige solicitação explícita. Posição e peso entram na síntese.
- Falhas Gemini não viram resposta local. Pareceres “manter/acompanhar” são aceitos;
  a síntese deixa de receber um inventário técnico anexado à resposta. Prompt 2.1.
- Chat, carteira, provedor e consentimento ficam visíveis; relatórios são secundários.
  Biblioteca, premissas e diagnóstico permanecem disponíveis por ações explícitas.
- **17 testes específicos aprovados**: PETR4, comparação, carteira completa,
  follow-up, conceito sem mercado, adapter Gemini Normal/DEMO, erro/consentimento,
  configuração externa e UI. Ruff e mypy dos oito módulos aprovados.
- Sem suíte completa, chamadas pagas ou validação autenticada. Uma compilação
  PyInstaller para atualizar o carregamento de configuração. O EXE foi gerado;
  a substituição da pasta em uso foi bloqueada pelo Windows. Os mesmos artefatos
  foram reunidos em `dist/Nexo-Hotfix`, sem recompilar ou fechar a instância aberta.

Execute da raiz com `.venv\Scripts\python.exe -m nexo.main` ou
`dist\Nexo-Hotfix\Nexo.exe`. Para abrir por duplo clique, coloque seu `.env` ao lado de
`Nexo.exe`. Com Gemini indicado no chat, marque a autorização e envie a pergunta.
