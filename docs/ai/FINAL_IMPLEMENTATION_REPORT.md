# Nexo — missão final de implementação e ajustes

Entrega de 03/11/2026, branch `feature/nexo-intelligence`.
[PR #1](https://github.com/Jujupedro5052005/nexo/pull/1), base `master`, sem merge.

## Resultado

A entrada do aplicativo agora oferece uma escolha visual entre Demo e Normal.
O NEXO Intelligence recebeu um copiloto vetorial com estados, conversa com nomes
legíveis, contexto em janela própria e relatório guiado. Planejamento, Metas e
Alertas recebem exemplos persistentes no DEMO. Análises apresenta caminhos claros
para patrimônio, simulações e educação. Relatórios inclui conferência mensal de
operações e simulação manual de IR. Há receita PyInstaller e executável Windows
em pasta, com biblioteca técnica incluída e segredos externos.

As telas mantêm azul escuro/ciano, componentes Qt e separação de camadas. O ledger,
providers, biblioteca de 15 capítulos e métodos financeiros anteriores continuam
disponíveis. Nenhuma ferramenta da IA executa ordens.

Validação: suíte completa com **820 aprovados e 2 ignorados**; regressão final de
interface/finanças com **28 aprovados**. Ruff, mypy, compilação e build aprovados.
Smokes nativos verificam seletor e ambientes isolados, com limites descritos abaixo.

## Melhorias de interface e problemas corrigidos

| Antes | Resultado |
|---|---|
| Contexto estreito disputava largura com o chat | Janela redimensionável de contexto, com rolagem, fundo escuro e retorno à conversa. |
| Nova conversa exibia ID técnico e aviso de interrupção | Nome legível, pergunta limpa, relatório invalidado e orientação de início. |
| Fundo herdado claro tornava labels ilegíveis | Superfícies do contexto e viewport recebem o tema Nexo explicitamente. |
| Relatório vazio com texto isolado | Dois cards explicam conteúdo esperado e próximos passos. Memória de cálculo aparece quando há cálculo. |
| Diagnóstico consumia altura com tabela e donut empilhados | Par responsivo, gráfico com altura limitada e tabela completa com rolagem. |
| Campos de IR ficavam depois de uma tabela extensa | Abas “Conferir operações” e “Simular imposto”, dentro de Relatórios. |
| Educação e ferramentas sem roteiro claro | “Guia e simuladores”, nomes orientados à ação, instruções e ligação com o Copiloto. |
| Configurações precedia a IA | NEXO Intelligence em penúltimo; Configurações por último, incluindo atalhos internos. |

A revisão utilizou capturas reais Qt em 1440×900 e 1180×720. As imagens de teste
usam bancos temporários e providers controlados, identificados como DEMO/fixtures;
não comprovam cotações atuais ou inferência real.

## Agente financeiro Nexo

`CompanionAvatar` desenha o personagem com QPainter, sem downloads ou dependência
de serviço externo. `CompanionCard` reúne personagem, mensagem curta e ação.
Estados: pronto, analisando, concluído, atenção e explicando. A animação usa timer
de 50 ms somente durante análise visível; esconder o componente ou desligar
“Animar” interrompe o timer. Não existe animação contínua em repouso.

O agente recebe eventos da UI; não toma decisões financeiras. Progresso vem do
orquestrador existente. “Como começar” oferece instruções locais. Na educação,
“Explicar este tema” prepara a pergunta no Copiloto, sem envio automático ou
autorização implícita de nuvem. A síntese analítica e os pareceres condicionais
preservam as regras da Missão 2.

## Entrada, navegação e DEMO

Sem argumentos, `python -m nexo.main` e `Nexo.exe` abrem o seletor. Cancelar não
compõe providers nem cria bancos. `--demo` e `--normal` continuam disponíveis para
uso direto; o professor não precisa desses argumentos.

Demo e Normal usam arquivos separados. Registros existentes do Normal são
preservados. Na primeira abertura de um DEMO sem exemplos complementares:

- Planejamento: renda fictícia de R$ 8.500, despesas de R$ 5.200 e capacidade
  mensal de aporte de R$ 3.300, no mês de criação dos exemplos.
- Metas: reserva de emergência, aporte de longo prazo e viagem, com progresso,
  prazo e aporte necessário sem juros. Valores das metas são manuais, não extraídos
  automaticamente das carteiras.
- Alertas: três condições de preço, inicialmente “DEMO · exemplo não avaliado”.
  A verificação continua manual e utiliza os providers existentes.

O seed complementar tem marcador versionado e transação. Reabrir não duplica
registros e não sobrescreve tabelas já preenchidas. A função só aceita o arquivo
`nexo_demo.db`, rejeitando links simbólicos. O seed não consulta APIs.
O mês do orçamento permanece o da criação; em apresentações posteriores, selecione
esse mês ou cadastre novos lançamentos.

Planejamento também oferece projeção com aportes e alocação manual entre objetivos.
As taxas e os percentuais são hipóteses editáveis; os pesos devem somar 100%.
O atalho “Simular aportes e alocação” leva diretamente ao simulador. Não movimenta
o caixa nem compra ativos. As barras de metas conservam a tabela detalhada.

Os exemplos de alertas cobrem preço. Eventos de calendário, variação percentual
e concentração não ganharam um motor automático de alertas nesta entrega.
Concentração continua disponível nas análises existentes.

## Análises, patrimônio e educação

As quatro entradas são análise de ativo, comparação de carteiras, patrimônio e
retorno, guia e simuladores. O workbench permanece carregado sob demanda.

Patrimônio/TWR explica caixa + ativos, fluxo externo e encadeamento diário do
retorno. Cards apresentam patrimônio, fluxo e TWR; o período compara primeiro
e último fechamento disponíveis. “Preparar caixa em Movimentações” abre o livro
de caixa. Ausência de saldo inicial ou preços suficientes mantém o resultado
indisponível, com motivo; custo de aquisição não é convertido em patrimônio.
O total de fluxos é calculado na camada de cálculos, com precisão Decimal.

O guia distingue simulações manuais, consultas de risco, modelos de solidez e
educação. Foram acrescentados temas de noções básicas e roteiro de análise aos
checklists anteriores. Marcar itens produz orientações, sem score de fraude ou
certificação de adequação. O personagem pode encaminhar o tema ao chat.

## Assistente de IR — incremento funcional e parcial

O módulo possui duas tarefas separadas:

1. Conferência anual por mês: vendas brutas, taxas pagas, resultado realizado e
   ativos. Reconstitui o histórico anterior ao ano para conservar preço médio
   e considera splits registrados no ledger. Exportação CSV preserva números
   exatos; taxas pagas não são deduzidas novamente do resultado realizado.
2. Simulação com resultado tributável, prejuízo compensável anterior, alíquota e
   IRRF informados pelo usuário. Calcula compensação, base, imposto estimado,
   valor do cenário após retenção e saldo de prejuízo. Valores inválidos, não
   finitos ou extremos são rejeitados.

O resultado contábil não vira base tributável automaticamente. O Nexo não conhece
corretora, modalidade fiscal, todas as carteiras do contribuinte ou elegibilidade
das compensações. Não classifica final 11 como FII, não presume isenção e não
fixa alíquotas legais. Não gera declaração, DARF ou obrigação de entrega.
O usuário confere modalidade e período antes de simular.

Fontes primárias consultadas: [Receita Federal — bolsa de valores](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1),
[apuração mensal](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1/demonstrativo-de-apuracao-de-ganhos)
e [compensações](https://www.gov.br/receitafederal/pt-br/assuntos/meu-imposto-de-renda/pagamento/renda-variavel/bolsa-de-valores-1/compensacoes).
São referências para conferência humana; este apoio não substitui contador ou
declaração oficial.

## Código e distribuição

| Área | Evidência principal |
|---|---|
| Entrada | `main.py`, `ui/dialogs/startup.py`, `launcher.py` |
| Agente/guia | `ui/components/companion.py` |
| IA/relatório | `ui/pages/intelligence_page.py`, `ui/components/intelligence_cards.py` |
| Navegação | `ui/windows/main_window.py` |
| DEMO | `infrastructure/database/demo_finances.py` |
| Planejamento/metas | `ui/pages/personal_finance.py`, `ui/components/planning_scenario.py`, `calculations/projections/planning.py` |
| Análises/TWR/educação | `ui/pages/analysis_page.py`, `ui/components/account_panel.py`, `research_workbench.py`, `application/education/checklists.py`, `calculations/valuation/performance.py` |
| IR | `application/portfolio/tax_worksheet.py`, `calculations/tax.py`, `ui/components/tax_panel.py`, `ui/pages/reports_page.py`, `application/portfolio/export_report.py` |
| Recursos/segredos | `core/paths.py`, configurações de mercado/IA, biblioteca |
| Build/smoke | `Nexo.spec`, `requirements-build.txt`, `scripts/smoke_executable.py` |

Caminhos sem prefixo de distribuição são relativos a `src/nexo`. A receita
PyInstaller usa distribuição em pasta, sem console, com QtCharts, SQLite e corpus.
Não inclui `.env`, bancos ou caches do usuário. Segredos são lidos do `.env`
externo ao lado do executável. Dados graváveis ficam em `%LOCALAPPDATA%\NexoInvest`
ou no `NEXO_DATA_DIR` absoluto já suportado. O corpus congelado usa `_MEIPASS`.

Documentação técnica consultada: [spec files](https://pyinstaller.org/en/stable/spec-files.html)
e [runtime](https://pyinstaller.org/en/stable/runtime-information.html) do PyInstaller.
[Como gerar e usar o executável](../04_development/WINDOWS_EXECUTABLE.md).

Distribuição local desta entrega: `dist/Nexo-Windows.zip`, com `Nexo/Nexo.exe`,
dependências, biblioteca, template de configuração sem chaves e instruções.
O ZIP não é versionado no Git. Verificação e hash no [registro de validação](FINAL_VALIDATION.md).

## Capturas

| Fluxo | 1440×900 | 1180×720 |
|---|---|---|
| Entrada | [Seletor](screenshots/final/startup-1440.png) | [Seletor](screenshots/final/startup-1180.png) |
| Nova conversa | [Copiloto](screenshots/final/new-conversation-1440.png) | [Copiloto](screenshots/final/new-conversation-1180.png) |
| Contexto | [Janela própria](screenshots/final/context-1440.png) | [Janela própria](screenshots/final/context-1180.png) |
| Relatório vazio | [Orientação](screenshots/final/report-empty-1440.png) | [Orientação](screenshots/final/report-empty-1180.png) |
| Relatório pronto | [Diagnóstico](screenshots/final/report-1440.png) | [Diagnóstico](screenshots/final/report-1180.png) |
| Planejamento | [Orçamento](screenshots/final/planning-1440.png) | [Orçamento](screenshots/final/planning-1180.png) |
| Simulador de aporte | [Cenários](screenshots/final/planning-scenario-1440.png) | [Cenários](screenshots/final/planning-scenario-1180.png) |
| Metas | [Progresso](screenshots/final/goals-1440.png) | [Progresso](screenshots/final/goals-1180.png) |
| Alertas | [Exemplos](screenshots/final/alerts-1440.png) | [Exemplos](screenshots/final/alerts-1180.png) |
| Patrimônio/TWR | [Guia](screenshots/final/performance-1440.png) | [Guia](screenshots/final/performance-1180.png) |
| Educação | [Temas](screenshots/final/education-1440.png) | [Temas](screenshots/final/education-1180.png) |
| IR: conferência | [Ledger](screenshots/final/tax-ledger-1440.png) | [Ledger](screenshots/final/tax-ledger-1180.png) |
| IR: simulação | [Calculadora](screenshots/final/tax-1440.png) | [Calculadora](screenshots/final/tax-1180.png) |

Referência anterior: [chat da Missão 2](screenshots/mission2/chat-1440.png) e
[relatório anterior](screenshots/mission2/report-1440.png).

## Validação e limites

O baseline desta missão passou com 800 testes e 2 smokes reais ignorados.
Resultados finais e distinção entre fixtures e execução nativa:
[FINAL_VALIDATION.md](FINAL_VALIDATION.md).

Os testes abrangem entrada sem flags, cancelamento, ambos os ambientes, navegação,
dados DEMO, isolamento do seed, estados/animação, contexto e nova conversa,
relatório, guias, TWR, educação, alocação, matemática fiscal, histórico de custos,
splits e CSV. Nenhum teste comum autoriza inferência paga.

Permanecem os limites analíticos e de integração descritos na
[Missão 2](MISSION_2_REPORT.md): aceite autenticado Gemini/File Search, catálogo
YouTube ampliado, autorização de conteúdo, dados macro/pares e classificação
setorial completa. Não houve processamento de vídeo ou indexação nesta missão.
Não houve auditoria de acessibilidade por leitor de tela, de todos os monitores/DPI
ou teste em uma instalação Windows limpa. O executável não é assinado.

## Roteiro recomendado para a apresentação

1. Abra Nexo e escolha Demo. Explique a separação do ambiente Normal.
2. Visite Carteiras/Movimentações e mostre a reconstrução das posições do ledger.
3. Abra Planejamento, simule aporte/alocação e depois mostre metas e alertas.
4. Em Análises, apresente o guia de patrimônio; prepare caixa antes de consultar
   TWR. Demonstre educação e o encaminhamento de um tema ao Copiloto.
5. No Copiloto, selecione a carteira, peça análise completa e explore relatório,
   fontes e cenários. Envio ao Gemini exige autorização e chave configurada.
6. Em Relatórios, confira um ano de operações e simule IR com premissas manuais.
   Exemplo didático: resultado 1.000, prejuízo 200, taxa 15%, IRRF 5 → cenário 115.
7. Mostre Configurações por último. Se a internet falhar, use ledger, orçamento,
   metas e simuladores; cotações ausentes não recebem preços fictícios.

Não reinicie ou apague bancos para demonstrar o modo Normal: use um diretório
de apresentação separado se quiser uma experiência vazia. Preserve o ambiente
do usuário. Para refletir código atualizado numa instância já aberta, feche e
reabra o aplicativo.
