# NEXO Intelligence — arquitetura implementada

Incremento autorizado em 03/11/2026, complementar ao núcleo acadêmico.

```text
IntelligencePage / TaskRunner
  -> IntelligenceWorkspace / IntelligenceOrchestrator
     -> KnowledgeRetriever (local textual OU Gemini File Search)
     -> IntelligenceProvider (mock OU Google Gen AI SDK)
     -> FinancialTools -> casos de uso existentes / providers compartilhados
                       -> calculations.valuation.intelligence (Decimal)
     -> IntelligenceStorage (SQLite dedicado)
```

`main.py` compõe as dependências com os mesmos serviços de mercado utilizados
pelas telas existentes. Nenhum adaptador financeiro alternativo foi introduzido.
O ledger, o schema financeiro, a reconstrução de posições e os budgets de mercado
continuam sob os componentes anteriores. A UI não executa HTTP ou SQL.

O modo de conversa possui uma recuperação documental, uma rodada de planejamento por
function calling, execução local validada e uma síntese sem ferramentas.
Não há ciclo autônomo ilimitado. O limite padrão é oito chamadas; comparações
contam suas consultas internas. `calculate_valuation` é acionada somente com
premissas explícitas da interface, sem permitir ao modelo inventar parâmetros.
As fontes e a memória de cálculo recebem um apêndice determinístico.

File Search e function calling ocorrem em chamadas separadas. Documentos são
dados não confiáveis, separados do system prompt versionado (`SYSTEM_PROMPT`,
versão 2.0 em `infrastructure/intelligence/providers.py`). Histórico remoto
limitado às últimas quatro mensagens, até 800 caracteres por mensagem.
Contexto excessivo gera erro compreensível, sem cortar JSON ou inventar dados.

`domain/models/intelligence.py` contém contratos Pydantic; os protocolos de
provedor, recuperação e persistência ficam em `domain/interfaces/intelligence.py`.
Herança implementa contratos de providers e componentes Qt; composição conecta
ferramentas, recuperação e orquestração. Não há subclasses por categoria de ativo.

`<nome_do_banco_financeiro>_intelligence.db` armazena conversas, documentos,
versões de metodologias, cache e uso. Normal: `data/nexo_intelligence.db`.
Demo: `data/nexo_demo_intelligence.db`. Uma conexão por operação, transações e
reserva de quota com `BEGIN IMMEDIATE`. Não há posições persistidas nesse banco.
Exportar/limpar o banco financeiro não inclui o banco da IA: a página oferece
limpeza própria das conversas/cache, preservando documentos e contadores.

Cancelamento é cooperativo, com descarte da resposta atrasada e checagem antes
de persistir o turno. Chamadas já aceitas pelo servidor podem consumir quota e
aguardam timeout de até 30 s. A aplicação espera os workers antes de fechar o SDK.
Não há streaming nesta versão; a resposta aparece após a conclusão.

Limites e evidências atuais: [MISSION_2_REPORT.md](MISSION_2_REPORT.md).

## Investigação aprofundada — Missão 2

`DeepAnalysis` coordena as ferramentas e casos de uso existentes. Antes do mercado,
limita o universo a 20 posições abertas e 100 chamadas lógicas. Consulta cotação,
fundamentos, proventos e histórico de um ano por ativo. Cache em memória de cinco
minutos evita repetir essas quatro consultas em revisões; caches/budgets dos
providers continuam válidos. A valorização inicial usa os serviços compartilhados.
Não há varredura ilimitada de oportunidades.

Perguntas naturais por preço teto e comparações identificam os tickers e mantêm
`focus_symbols` nos follow-ups. Isso evita investigar toda a carteira por uma
pergunta específica. Pedir toda a carteira remove o foco restrito. Alterar o
ativo selecionado impede herdar o foco anterior.

O relatório determinístico contém exposição, correlação, histórico, cenários,
pareceres e evidências. `calculations/valuation/bank.py` e
`calculations/risk/correlation.py` concentram matemática reutilizável. Com
estimativas e envio autorizados, Gemini propõe três conjuntos tipados de hipóteses.
Limites e Ke > g são validados localmente. Só métodos nativos aprovados calculam;
o LLM não cria fórmulas executáveis.

Recuperação, proposta estruturada e síntese são chamadas separadas. A síntese
recebe evidências compactas, sem séries completas. Os 15 capítulos ficam fora
do system prompt. A proteção de qualidade rejeita cópias longas dos trechos e
atribuições a vídeos sem fonte processada. Falha/quota na síntese preserva o
relatório local com aviso e modo `local-fallback`.

`conversation_context` persiste escopo, hipóteses e resumo do relatório anterior
por conversa/contexto. Mudar carteira limpa a apresentação e impede vazamento
entre escopos. Nenhuma tabela financeira foi alterada. Exportação humana é
Markdown; diagnóstico JSON requer ação explícita.

Corpus canônico: `docs/ai/knowledge`; wheel: `share/nexo/knowledge`. A carga
deduplica hashes e marca versões anteriores como inativas. File Search é índice
reconstruível gerenciado por CLI, sem sincronização remota ao iniciar.
