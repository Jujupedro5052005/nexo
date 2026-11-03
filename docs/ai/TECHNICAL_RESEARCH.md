# Pesquisa técnica — 03/11/2026

Pesquisa em documentação oficial, sem geração Gemini, sem indexação remota e
sem habilitar faturamento. Documentação online pode mudar; disponibilidade no
projeto é confirmada por teste de metadados e, opcionalmente, smoke autorizado.

| Tema | Conclusão e decisão |
|---|---|
| SDK Python | Usar `google-genai>=1.75,<2`, não o SDK legado. Cliente lazy, timeout e retentativas controladas pelo aplicativo. |
| Modelo | A documentação consultada apresenta `gemini-3.5-flash-lite` como opção econômica estável, com texto, vídeo, function calling, structured outputs e File Search. É o padrão configurável, sem recorrer automaticamente a modelos mais caros. |
| Modelos por tarefa | Conversa, extração, vídeo e recuperação têm variáveis independentes. O padrão econômico é compartilhado até haver evidência de necessidade de outro modelo. |
| Compatibilidade | Recursos e combinações variam por geração. Mesmo havendo suporte documentado a combinações nas gerações recentes, recuperação e function calling ficam separados para reduzir dependências. |
| Function calling | O modelo sugere nomes/argumentos. O Nexo decide o que executar, valida Pydantic e não habilita chamadas automáticas do SDK. `parameters_json_schema` preserva o contrato JSON Schema, incluindo limites exclusivos. |
| Structured outputs | Extração usa schema Pydantic, validação local e revisão obrigatória. JSON válido não equivale a metodologia verdadeira ou aprovada. |
| File Search | Indexação persistente em store configurado; recuperação retorna grounding e referências. A indexação de embeddings pode ser cobrada, portanto exige autorização separada. Não há upload por pergunta. |
| Vídeos | A API documenta entrada por URL pública do YouTube. O pipeline só envia URL selecionada e autorizada, com contagem prévia de tokens e lote unitário. Não baixa vídeo/legenda. |
| AI Studio | Nome, ID e número do projeto não são credenciais. A chave seleciona o projeto autorizado no backend; os identificadores locais são informativos. |
| Cotas | Quotas do Gemini dependem do modelo, tier e projeto. Limites locais conservadores não substituem o controle do Google; 429 não é contornado. |
| Preços | Não fixar tabela de preços no código. Tarifas opcionais por milhão permitem uma estimativa conservadora; a fatura do Google é a referência real. Sem tarifa, custo aparece indisponível. |
| Privacidade | Verificar condições do tier no AI Studio antes de enviar documentos ou dados financeiros. O tratamento de dados pode diferir entre modalidades gratuitas e pagas. |
| YouTube API | `channels.list(forHandle)` confirma um ID esperado; uploads por `playlistItems.list`; detalhes por `videos.list`. Evita busca por nomes semelhantes. |
| Conteúdo | Metadados públicos não concedem licença de transcrição. Direitos de processamento/retenção são registrados separadamente. Metadados do catálogo expiram em 29 dias e precisam de nova consulta. |

Canal: o endpoint oficial
[oEmbed do vídeo público](https://www.youtube.com/oembed?url=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3DkgPS0FMp2D4&format=json)
retornou `author_name=Geração Dividendos` e
`author_url=https://www.youtube.com/@geracaodividendoss` nesta sessão.
O handle possui dois “s” no final. O ID `UC…` não foi confirmado pela Data API
sem credencial YouTube; o catálogo exige esse ID explicitamente e valida sua
correspondência antes de importar. Nenhum vídeo foi processado ou atribuído às
metodologias nativas. Não foram utilizadas páginas de download nem scraping.

Referências oficiais consultadas:

- [Google Gen AI Python SDK](https://googleapis.github.io/python-genai/)
- [Modelos](https://ai.google.dev/gemini-api/docs/models), [Flash-Lite](https://aistudio.google.com/docs/models/gemini-3.5-flash-lite) e [descontinuações](https://ai.google.dev/gemini-api/docs/deprecations)
- [Chaves e AI Studio](https://ai.google.dev/gemini-api/docs/api-key)
- [Function calling](https://ai.google.dev/gemini-api/docs/function-calling)
- [Structured outputs](https://ai.google.dev/gemini-api/docs/structured-output)
- [File Search](https://ai.google.dev/gemini-api/docs/file-search)
- [Video understanding](https://ai.google.dev/gemini-api/docs/video-understanding)
- [Preços](https://ai.google.dev/gemini-api/docs/pricing), [cotas](https://ai.google.dev/gemini-api/docs/rate-limits) e [termos](https://ai.google.dev/gemini-api/terms)
- [YouTube channels.list](https://developers.google.com/youtube/v3/docs/channels/list), [playlistItems.list](https://developers.google.com/youtube/v3/docs/playlistItems/list), [videos.list](https://developers.google.com/youtube/v3/docs/videos/list)
- [Políticas YouTube](https://developers.google.com/youtube/terms/developer-policies)

O teste de transporte usa o SDK real com `httpx.MockTransport`: verifica
serialização efetiva sem contactar o Google. Isso não comprova permissões nem
disponibilidade remota do modelo no projeto do usuário.

## Pesquisa e revalidação — Missão 2

Referências primárias: Damodaran/NYU, BCB IF.data/juros, IBGE/IPCA, CVM, SUSEP,
ANEEL, B3 e RI das companhias, listadas por tema na [biblioteca](knowledge/README.md).
Textos e exemplos são originais; taxas sintéticas não representam mercado atual.
Desconto, retorno excedente e correlação têm testes com valores conhecidos.
Não se alega certificação regulatória ou revisão independente do corpus.

Os dois endpoints oficiais oEmbed confirmaram títulos/autoria:
[Nunca mais compre um banco caro!](https://www.youtube.com/oembed?url=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3D7wOGP2bklNc&format=json)
e [Calculei o preço teto do Itaú e o resultado me surpreendeu](https://www.youtube.com/oembed?url=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3D_CVsSXQ6NMc&format=json).
Ambos identificam `@geracaodividendoss`. Isso não confirma conteúdo, data,
duração, licença ou ID UC. Zero vídeos processados.

Recuperação, function calling e proposta estruturada ficam separados. Contratos
de stores/cenários foram exercitados com clientes simulados, sem comprovar
permissões ou disponibilidade remota do modelo.

O ciclo de vida dos gráficos foi revisado com a documentação
[QAreaSeries](https://doc.qt.io/qt-6/qareaseries-qtcharts.html) e
[QChartView](https://doc.qt.io/qt-6/qchartview-qtcharts.html). A view retém wrappers,
fronteiras têm pai explícito e o construtor usa a sobrecarga upper/lower.
Um teste força coleta de lixo e descarte de widgets em substituições repetidas.
