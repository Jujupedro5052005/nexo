# Segurança e privacidade

- Chave lida de `GEMINI_API_KEY`, excluída do repr e da serialização das
  configurações; não entra no histórico, em logs ou mensagens de erro.
- Nenhum SQLite integral é enviado. A carteira precisa ser selecionada; os
  nomes das demais carteiras não são expostos ao modelo. O histórico consultável
  por ferramenta é limitado a dez movimentações por padrão, no máximo vinte.
- Antes do envio, a UI descreve o contexto transmitido e exige autorização:
  pergunta, últimas quatro mensagens resumidas, documentos recuperados e
  evidências financeiras do contexto selecionado. A seleção é opcional.
- `NEXO_AI_ENABLED=false` desativa o agente; `NEXO_AI_PROVIDER=mock` mantém o
  processamento de linguagem local. Consultas financeiras selecionadas continuam
  usando os providers existentes, com seus próprios limites/cache.
- Documentos e histórico são dados não confiáveis em campos próprios. O system
  prompt não é concatenado ao texto de documentos. Tentativas de executar SQL,
  shell, Python ou acessar outra carteira são rejeitadas pela lista de ferramentas.
- Fórmulas externas nunca se tornam código. Com consentimento, o LLM pode propor
  hipóteses tipadas e limitadas, identificadas como estimadas. Matemática fica
  local e cotações operacionais têm prioridade.
- Markdown não carrega imagens/arquivos embutidos; links externos só abrem por
  clique e com esquema HTTP/HTTPS. Links `file:`, `javascript:` e similares não
  são encaminhados ao sistema operacional.
- Erros externos são convertidos em mensagens seguras, sem corpos HTTP nem URLs
  autenticadas. A memória de cálculo e os indicadores permanecem rastreáveis.
- Não há ferramentas de compra/venda, alteração de ledger, envio de ordens ou
  comunicação com terceiros.

Histórico e documentos ficam em SQLite local separado, em texto legível; não há
criptografia própria nem autenticação multiusuário. Use permissões e proteção
de disco do sistema operacional. A página oferece apagar conversas/cache e
excluir documentos. Contadores não são apagados para contornar quotas.
O backup financeiro existente não inclui o banco da IA; feche o aplicativo antes
de copiar seu banco de conversas separadamente.

Uso local: reservas atômicas, falhas contabilizadas conservadoramente, uma
retentativa de 429 e limites por solicitação/dia. O contador local não é a fatura
Google. File Search pode incluir tokens recuperados pelo servidor além da
estimativa local de texto; metadados reais são registrados quando disponíveis.
Não há garantia de um teto monetário de faturamento remoto. Configure também
os controles do projeto Google se precisar de limites externos.

Prompt injection não possui solução absoluta por instrução textual. A barreira
executável é a validação de ferramentas e a ausência de ações financeiras ou
de execução livre. Prosa gerada ainda pode conter erro e exige avaliação humana.
Consulte as condições do seu tier Gemini antes de enviar dados sensíveis.
