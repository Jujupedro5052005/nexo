# Entrega final Windows — 04/11/2026

Versão de entrega: `0.1.0-final-20261104`. Base Git:
`2150a371955d490f63ca9fb50a00ea4fe4df0f1f`, acrescida das alterações locais
incluídas em `Projeto/`. Não houve commit, push ou merge.

## Resultado

Aceite nativo aprovado no Windows 10 build 19045, usando o **EXE extraído do ZIP**,
com diretório gravável temporário, IA mock sem perguntas enviadas e budgets de
mercado zero. Os provedores do aplicativo continuam sendo os reais nos dois modos.

- HTML local aprovado: 14 slides; Home/seta direita, slide 2, tour na Visão Geral
  e retorno ao mesmo slide. Pausa/retomada e foco também cobertos no WebEngine real.
- Tela cheia pelo botão do HTML e saída por Escape restauraram 1440×900 e a barra.
- Configurações e NEXO Intelligence acessíveis; educação compacta e legível.
- Ícone conferido na janela, seletor, barra de tarefas, Alt+Tab e pelo ícone do EXE
  fornecido pelo Explorer. Barra escura com controles claros no Windows 10.
- Duplo clique para maximizar/restaurar; arraste da janela restaurada; resize
  físico de 1440 para 1480 pixels; minimizar/restaurar; fechar e reabrir aprovados.
- Seletor e modo de demonstração também executados pelo smoke existente.
  O demo criou somente seus exemplos temporários e carregou os 15 documentos de IA.
- Bancos pessoais: quatro arquivos conferidos por SHA-256 antes/depois, intactos.
  No ambiente normal temporário, carteiras, eventos e transações continuaram com
  zero registros após a navegação e a reabertura. Nenhuma operação foi registrada.
- Zero inferências pagas; nenhum pedido remoto de mercado autorizado pelo smoke.

Hash do executável, resultados e observações:
[`final_executable_smoke.json`](final_executable_smoke.json).
Capturas selecionadas: [`final_review/`](final_review/).

## Verificações de desenvolvimento e pacote

Regressões direcionadas de navegação, configurações e empacotamento:
27 aprovadas e uma ignorada por falta de suporte a links simbólicos. Apresentação
real: quatro testes aprovados, incluindo troca síncrona de página durante o tour
e entrada/saída de tela cheia pelo teclado. Quatro verificações complementares de
companheiro, caminhos congelados, cancelamento da entrada e preferências passaram.

Ruff, mypy (162 arquivos), compileall e `git diff --check` aprovados.
Revisão de layout em 1180×720 e 1440×900; escala adicional por
`QT_SCALE_FACTOR=1.25`, sem alterar a configuração de DPI pessoal do Windows.

Build limpo com PyInstaller, sem desabilitar sandbox. O verificador do pacote
compara métodos críticos do PYZ com o checkout, evitando módulos antigos em cache;
confere também os recursos offline e o corpus. HTML, PDF e ícones preservam os
hashes do kit original. As proteções existentes rejeitam bancos e credenciais.
O ZIP inclui fontes, testes, scripts, docs, exemplos de configuração e contingências.

## Pendências e limites

**Planilha oficial de avaliação não encontrada no checkout nem no kit.** Anexar
a planilha fornecida pelo professor antes de entregar; nenhuma substituta foi criada.

O caminho DWM de Windows 11 está protegido e tipado, mas não foi executado neste
Windows 10. Não houve validação em instalação Windows limpa ou assinatura digital.
Escala Windows real de 125% não foi alterada; a verificação adicional usou escala Qt.
