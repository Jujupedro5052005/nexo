# NEXO Intelligence — entrega da Missão 2

Data: 03/11/2026. Branch: `feature/nexo-intelligence`.
PR: [#1 — NEXO Intelligence](https://github.com/Jujupedro5052005/nexo/pull/1),
base `master`, sem merge. Este documento substitui o relatório histórico da
Missão 1 como descrição do estado atual.

## 1. Resumo executivo

O Nexo agora oferece chat prioritário, contexto recolhível, relatório financeiro
visual, investigação limitada da carteira e cenários assistidos auditáveis.
Preservou azul escuro/ciano, componentes existentes, providers e ledger.
Os 15 documentos técnicos foram escritos e integrados à biblioteca local;
File Search é um índice remoto opcional desses mesmos documentos.

Pareceres podem favorecer ou desaconselhar ampliação sob condições explícitas.
Matemática é local e determinística; a IA interpreta evidências e pode propor
hipóteses tipadas. Nenhuma ferramenta executa operações financeiras.

## 2. Capturas antes e depois

Capturas reais do aplicativo Qt, com fixtures financeiras sintéticas e banco
temporário. Não representam patrimônio do usuário nem teste de inferência real.

| Área | Evidência |
|---|---|
| Antes da reformulação | [Antes](screenshots/mission2/before.png) |
| Copiloto | [1440×900](screenshots/mission2/chat-1440.png), [1180×720](screenshots/mission2/chat-1180.png) |
| Diagnóstico da carteira | [1440×900](screenshots/mission2/report-1440.png), [1180×720](screenshots/mission2/report-1180.png) |
| Cards e cenários | [1440×900](screenshots/mission2/asset-cards-1440.png), [1180×720](screenshots/mission2/asset-cards-1180.png) |
| Biblioteca | [1440×900](screenshots/mission2/library-1440.png), [1180×720](screenshots/mission2/library-1180.png) |

## 3. Experiência de uso

- Copiloto é a aba inicial, com sugestões e compositor sempre acessível.
- Enter envia; Shift+Enter cria nova linha. Há nova conversa, contexto e progresso.
- Seleção de carteira/ativo, consentimento e opções ficam no painel recolhível.
- Relatório mostra indicadores, exposição setorial, donut, cenários e histórico.
- Biblioteca permite filtro, leitura Markdown e fichas de metodologia.
- JSON fica no inspetor técnico e na exportação diagnóstica explícita.
- Relatório humano é exportado em Markdown. PDF não foi implementado.
- Contexto mudado limpa resultados e descarta respostas tardias.

## 4. Código alterado

| Camada | Arquivos principais e finalidade |
|---|---|
| Application | `application/intelligence/deep_analysis.py`: investigação, cache, evidências e cenários; `orchestrator.py`: intenção, follow-ups e síntese; `synthesis_quality.py`: qualidade mínima; `report_export.py`: relatório humano. |
| Application | `methodologies.py`: método bancário aprovado; `knowledge_service.py`: IDs reservados; `workspace.py`: exportação separada. |
| Calculations | `calculations/valuation/bank.py`: retorno excedente; `calculations/risk/correlation.py`: correlação Decimal alinhada. |
| Domain | `domain/models/intelligence.py`: modos, foco e cenários tipados; `domain/interfaces/intelligence.py`: estado conversacional persistido. |
| Infrastructure | `infrastructure/intelligence/providers.py`: prompt v2 e proposta tipada; `knowledge.py`: corpus e stores/sincronização; `storage.py`: contexto; `cli.py`: administração explícita; `youtube.py`: catálogo até 30 e preservação de permissões; `composition.py`: carga local e modo normal/demo. |
| Mercado | `infrastructure/market_data/adapters/yahoo.py`: zero intradiário vira ausência; horário de consulta não substitui horário de mercado. |
| UI | `ui/pages/intelligence_page.py`; `ui/components/chat_composer.py`, `intelligence_cards.py`, `charts.py`; `ui/windows/main_window.py`. |
| Composição/distribuição | `main.py`: modo demo explícito; `pyproject.toml`: corpus no wheel, mantendo uma única fonte documental. |
| Testes | `tests/intelligence/test_mission2.py`, `test_mission2_portfolio.py`, `test_mission2_integrations.py`, `tests/ui/test_chart_lifetime.py`; ajustes nas fixtures e expectativas de prompt/catálogo existentes. |

Todos os caminhos de código acima são relativos a `src/nexo`, salvo testes e
`pyproject.toml`. Não houve migração ou alteração de schema financeiro.

## 5. Documentos técnicos

Quinze capítulos originais em português, aproximadamente 11 mil palavras no
total, com fórmulas, exemplos sintéticos, limitações, critérios de uso e fontes.
Nenhum é transcrição de vídeo ou inclusão no system prompt.

1. [Fundamentos de valuation](knowledge/foundations/01_fundamentos.md).
2. [Dividendos, DDM e Gordon](knowledge/valuation/02_gordon.md).
3. [Preço teto por yield alvo](knowledge/valuation/03_yield_alvo.md).
4. [Múltiplos e comparabilidade](knowledge/valuation/04_multiplos.md).
5. [Bancos e retorno excedente](knowledge/sectors/05_bancos.md).
6. [Seguradoras e holdings](knowledge/sectors/06_seguros_holdings.md).
7. [Energia e utilities](knowledge/sectors/07_utilities.md).
8. [Cíclicas e commodities](knowledge/sectors/08_ciclicas.md).
9. [Fundos imobiliários](knowledge/sectors/09_fiis.md).
10. [Carteiras, exposição e risco](knowledge/portfolio/10_carteiras.md).
11. [Sustentabilidade da renda](knowledge/portfolio/11_renda.md).
12. [Contexto macroeconômico](knowledge/macro/12_macro.md).
13. [Crescimento e reinvestimento](knowledge/valuation/13_crescimento.md).
14. [Histórico, eventos e comparabilidade](knowledge/foundations/14_historico.md).
15. [Pareceres e critérios de revisão](knowledge/recommendations/15_pareceres.md).

Hash, caminho canônico e versão permitem atualizar sem substituir comportamento
do agente. Referência revisada não equivale a fórmula executável aprovada.

## 6. Referências

Referências específicas estão em cada capítulo. Fontes primárias consultadas:

- [Damodaran/NYU — valuation](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/valuation/val.htm), [instituições financeiras](https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/finfirm09.pdf) e [DDM](https://people.stern.nyu.edu/adamodar/pdfiles/eqnotes/ddm.pdf).
- [BCB IF.data](https://www3.bcb.gov.br/ifdata/) e [histórico de juros](https://bcb.gov.br/controleinflacao/historicotaxasjuros).
- [IBGE — IPCA](https://www.ibge.gov.br/estatisticas/economicas/precos-e-custos/9256-ipca.html).
- [CVM — dados dos regulados](https://www.gov.br/cvm/pt-br/acesso-a-informacao-cvm/perguntas-frequentes-da-cvm/como-acessar-dados-informacoes-sobre-regulados) e [Resolução 20](https://conteudo.cvm.gov.br/legislacao/resolucoes/resol020.html).
- [SUSEP — painéis](https://www.gov.br/susep/pt-br/central-de-conteudos/central-de-paineis), ANEEL, B3 e RI de companhias, conforme referências setoriais.
- [Google Gen AI SDK](https://googleapis.github.io/python-genai/), [function calling](https://ai.google.dev/gemini-api/docs/function-calling), [File Search](https://ai.google.dev/gemini-api/docs/file-search), [YouTube Data API](https://developers.google.com/youtube/v3/docs/).
- [Qt QAreaSeries](https://doc.qt.io/qt-6/qareaseries-qtcharts.html) e [QChartView](https://doc.qt.io/qt-6/qchartview-qtcharts.html), para propriedade dos gráficos.

Consultar essas fontes não alimentou automaticamente fatos macroeconômicos
atuais no aplicativo. O relatório indica quando macro não foi consultada.

## 7. Metodologias e rastreabilidade

Executáveis nativos: Gordon, yield alvo e múltiplos já existentes, mais retorno
excedente bancário `VPA × (ROE − g)/(Ke − g)`. Há sensibilidade manual, risco
histórico e nova correlação sobre intervalos coincidentes de séries ajustadas.

No modo assistido, bancos reconhecidos usam VPA/ROE observados; demais emissores
reconhecidos podem usar distribuição histórica com repetição futura expressamente
estimada. JCP identificado é excluído. Distribuição genérica permanece bruta e
não recebe espécie inventada. Três cenários registram entradas, fórmula, origem,
desconto e justificativas. Defaults de taxas são política ilustrativa versionada,
nunca taxas de mercado. Propostas Gemini têm schema e validação local.

O parecer compara cotação e teto estimado e avalia concentração/qualidade dos
dados. Acima de 25% por posição, o relatório sinaliza cautela de ampliação,
com limiar ilustrativo explícito. Não é venda automática, adequação pessoal ou
regra universal. Sem evidência suficiente, o parecer aguarda confirmação.
Não há probabilidades ou certeza de evolução de preço.

## 8. Catálogo de vídeos

**2 referências verificadas via oEmbed oficial; 0 vídeos processados; 0 registros
coletados pela Data API nesta sessão.**

| ID | Título oficial verificado |
|---|---|
| `7wOGP2bklNc` | Nunca mais compre um banco caro! |
| `_CVsSXQ6NMc` | Calculei o preço teto do Itaú e o resultado me surpreendeu |

Ambos retornaram autoria Geração Dividendos e handle `@geracaodividendoss`.
Datas/durações/ID UC não foram confirmados. Registros `reference_only`, sem
autorização, expiram em 29 dias. Títulos não comprovam metodologia ensinada.
O catálogo oficial até 30 está implementado/testado; preenchê-lo com 20–30 itens
permanece pendente de `YOUTUBE_API_KEY`, ausente no ambiente consultado, e ID UC
confirmado. Processamento exige autorização escrita específica e consentimento
de nuvem. Não houve scraping, download ou armazenamento de transcrição.

## 9. File Search

Criar/listar/selecionar stores, indexar, consultar, sincronizar por hash e excluir
documentos são suportados pela infraestrutura/CLI. Sincronização tem lote máximo
3; listagem limita 20 stores. Operação pendente não é reenviada; envio de estado
incerto exige reconciliação. Versão canônica inativa não fundamenta recuperação.

SDK e falhas foram testados com clientes controlados. **Nenhum store foi criado,
nenhum documento indexado remotamente e nenhuma recuperação autenticada real
foi executada.** Compatibilidade do modelo/projeto precisa desse aceite externo.
Não há combinação File Search/function calling em uma mesma chamada.
Comandos: [KNOWLEDGE_PIPELINE](KNOWLEDGE_PIPELINE.md).

## 10. Capacidades efetivamente testadas

- Carteira SQLite temporária com três ativos, todos investigados, exposição,
  concentração, histórico, correlação, três cenários e verificação por múltiplos.
- Pergunta pelo preço teto de ITUB4, sem premissas manuais nem ticker em campo.
- Comparação PETR4/PRIO3 e follow-up mantendo os dois ativos.
- Margem alterada para 25%, com recálculo e escopo mantido.
- Pergunta por ativo selecionado sem investigar todas as posições da carteira.
- Desativação de estimativas, ausência sem zero e classificação desconhecida
  sem inferir FII do final 11.
- Pergunta conceitual sem consulta financeira, inclusive se proposta pelo modelo.
- Cache, limites antes do mercado, erro/quota Gemini preservando relatório local.
- Carga/dedup/recuperação dos 15 capítulos, contratos de stores, sincronização,
  revisão, catálogo/autorização e proteção contra instruções em documentos.
- UI em duas dimensões, Enter/Shift+Enter, contexto, JSON oculto, exportação humana.
- Bancos temporários, sem alteração de transações e separação explícita DEMO.

São testes com evidências controladas; não comprovam rentabilidade, qualidade
de uma tese real ou disponibilidade do serviço no projeto do usuário.

## 11. Validação

Baseline antes da Missão 2: **765 aprovados / 2 ignorados** (397,47 s).
Primeira suíte completa após reformulação: **794 aprovados / 2 ignorados**
(427,58 s). Segunda suíte completa, com os ajustes de escopo/proveniência:
**799 aprovados / 2 ignorados** (405,99 s). Após os últimos ajustes de
apresentação e troca de ativo, regressão final de IA:
**111 aprovados / 2 ignorados** (16,13 s), incluindo novas capturas Qt.

Uma execução intermediária encontrou violação de acesso nativa do Qt em
`QAreaSeries`. Foram explicitados sobrecarga, propriedade e retenção dos wrappers;
adicionado teste de 45 substituições com coleta de lixo/descarte. A suíte completa
subsequente passou. Isso não equivale a garantia para todos os drivers/DPI.

Ruff, diff-check e compileall aprovados; mypy aprovado em **153 arquivos**. Wheel
construído e inspecionado: os 15 capítulos têm conteúdo idêntico ao canônico,
com manifesto de fontes incluído. Teste cobre fallback da biblioteca instalada.
Testes reais Gemini continuam desativados por padrão. Um aviso de depreciação
do SDK Google/Python permanece, sem falhas de teste associadas.

## 12. Consumo e preservação

Zero inferências Gemini, indexações File Search, processamento de vídeo ou
chamadas financeiras de produção executados para validar esta missão.
Houve consultas web às referências e aos metadados oficiais oEmbed, além de
dependências de build do wheel. Nenhuma cobrança de IA foi autorizada/iniciada.
Os testes usam mocks/transportes simulados e bancos temporários.
`.env`, chaves e bancos financeiros originais foram preservados e não entram
no commit. O projeto Google informado permanece nos defaults existentes.

## 13. Limitações e pendências

- Aceite autenticado de Gemini/File Search e orçamento externo pendentes.
- Catálogo ampliado depende da chave YouTube; nenhum conhecimento de vídeo foi
  adquirido nesta entrega.
- Investigação limitada a 20 ativos/100 chamadas lógicas. Providers mantêm seus
  próprios limites; falhas não são preenchidas com preços fictícios.
- Classificação setorial cobre cadastro restrito; outros ficam desconhecidos.
- Macro/notícias atuais, consenso, pares e curvas de taxas não são consultados
  automaticamente. Não há screener de todo o mercado, DCF setorial completo,
  reconstrução causal de eventos ou adequação regulatória.
- Hipóteses de recorrência, ROE e taxas precisam de revisão humana. Dados ausentes,
  antigos ou de espécie genérica limitam a força do parecer.
- Síntese pode exceder contexto/quota e cair no relatório determinístico local.
  Checagens de qualidade são heurísticas; não provam veracidade da prosa.
- File Search administrado pela CLI, sem gerenciador de stores na GUI. Uploads
  incertos não têm reconciliação automática. Busca local é textual.
- Corpus é original/revisado nesta implementação; revisão especializada
  independente permanece recomendada. Não se alega certificação.
- Sem streaming, PDF, testes exaustivos de DPI ou cálculo de probabilidades.

## 14. Configuração Windows

Na raiz `T:\nexo`, instale e execute:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m nexo.main
```

Inclua `GEMINI_API_KEY=SUA_CHAVE_LOCAL` no `.env` existente, somente se ainda
não estiver configurada; preserve as demais entradas e reinicie. Não cole chave
no chat/repositório. `auto` usa Gemini quando há chave; `mock` força offline.
Abra NEXO Intelligence, selecione contexto e autorize envio antes de analisar
com Gemini. Estimativas podem ser desativadas. Teste de conexão consulta
metadados, sem geração. Biblioteca local não exige store remoto.

[Configuração completa](GEMINI_SETUP.md), [metodologias](METHODOLOGIES.md),
[File Search/YouTube](KNOWLEDGE_PIPELINE.md), [testes](TESTING.md).

## 15. Pull Request

[PR #1 — NEXO Intelligence](https://github.com/Jujupedro5052005/nexo/pull/1).
Alterações preparadas na branch existente; não há merge automático.
