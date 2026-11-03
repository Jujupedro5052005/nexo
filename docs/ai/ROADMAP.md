# Roadmap do incremento

Entregue:

- Página PySide6 integrada, workers, Markdown protegido, histórico e cancelamento.
- Provedor mock e adaptador Gemini configurável por chave externa.
- Ferramentas financeiras somente leitura, sem integração redundante de mercado.
- Gordon, yield alvo e múltiplos com validação e sensibilidade determinística.
- Biblioteca local, extração estruturada, revisão/versionamento de metodologias.
- File Search opcional com grounding, dedup, operação incremental e exclusão.
- Catálogo YouTube oficial limitado, verificação de identidade, autorização e
  processamento por URL selecionada com contagem prévia de tokens.
- Cotas locais persistentes, retentativas limitadas, cache e estimativa opcional.
- Suíte sem rede e smokes externos explicitamente opt-in.

Aceite externo pendente, sem bloquear o uso local:

- Usuário incluir chave Gemini no `.env` e executar teste de conexão.
- Validar geração real no modelo disponível no projeto informado.
- Configurar store File Search existente e autorizar eventual indexação paga.
- Fornecer chave YouTube, confirmar ID UC e obter autorização do titular.
- Validar extração real e revisar manualmente as metodologias resultantes.

Evoluções recomendadas:

- Melhorar ajuda e predefinições revisadas dos formulários de premissas existentes.
- Streaming com interrupção no transporte, além do cancelamento cooperativo.
- UX de paginação e atualização de catálogo, com orçamento por lote explícito.
- Busca vetorial local intercambiável e suporte a PDF autorizado com extração.
- Curadoria transacional com trilha detalhada de revisões e reconciliação
  automatizada de operações remotas incertas.
- Avaliações de qualidade de respostas com corpus financeiro revisado.
