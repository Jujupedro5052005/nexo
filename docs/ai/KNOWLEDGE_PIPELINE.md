# Biblioteca, catálogo e processamento autorizado

A interface permite importar TXT/Markdown UTF-8 até 200 KB, pesquisar a biblioteca
e revisar metodologias. A importação pede autorização de processamento/retenção.
Hash SHA-256 deduplica conteúdo; alterações criam nova versão identificável.
A recuperação local é textual por trechos, sem dependência de embeddings pagos.
Isso não é apresentado como busca semântica local. File Search fornece a opção
semântica remota, sem mudar o contrato `KnowledgeRetriever`.

CLI equivalente no Windows:

```powershell
$ai = '.\.venv\Scripts\python.exe'
& $ai -m nexo.infrastructure.intelligence.cli status
& $ai -m nexo.infrastructure.intelligence.cli import-document .\meu-documento.md --authorized
& $ai -m nexo.infrastructure.intelligence.cli list
& $ai -m nexo.infrastructure.intelligence.cli extract HASH --allow-cloud
& $ai -m nexo.infrastructure.intelligence.cli review ID 1 --reviewer 'Seu nome' --approve
```

No Linux, substitua `& $ai` por `.venv/bin/python`. Para o demo ou um banco
isolado, use `--database /caminho/absoluto/banco_intelligence.db` antes do comando.
Nunca use o banco financeiro como destino da CLI.

Indexação opcional, após criar/selecionar um store e autorizar
eventual cobrança de embeddings:

```powershell
& $ai -m nexo.infrastructure.intelligence.cli index HASH --allow-paid-indexing
& $ai -m nexo.infrastructure.intelligence.cli delete-document HASH
```

`index` registra a operação remota. Se retornar `pending`, repita o mesmo comando
para consultar a conclusão, sem novo upload. Documento já indexado retorna seu
nome remoto. Um envio de resultado incerto bloqueia novas submissões até
reconciliação manual no store; exclusão espera a indexação terminar e remove o
remoto antes do local. A GUI impede apagar apenas o registro local indexado.
Documentos antigos continuam disponíveis até exclusão explícita de seu hash;
esse histórico não é silenciosamente descartado numa atualização.

YouTube:

1. O handle identificado é `@geracaodividendoss`; confirme o ID `UC…` oficial.
2. Habilite/configure a YouTube Data API por sua conta, com `YOUTUBE_API_KEY`.
3. Execute um lote pequeno; máximo de trinta vídeos e três consultas de metadados
   por lote (canal, uploads, detalhes). Sem paginação automática de centenas.
4. Cadastre autorização escrita do titular para o vídeo selecionado.
5. Processe um único vídeo por chamada; contagem prévia de tokens bloqueia vídeos
   acima do limite. URL pública é enviada diretamente ao Gemini, sem download.

```powershell
& $ai -m nexo.infrastructure.intelligence.cli catalog-youtube --confirmed-channel-id UC_ID_CONFIRMADO --limit 5
& $ai -m nexo.infrastructure.intelligence.cli authorize-video youtube_VIDEO_ID --permission-reference 'Documento de autorização do titular'
& $ai -m nexo.infrastructure.intelligence.cli process-video youtube_VIDEO_ID --allow-cloud
```

Sem autorização, apenas metadados permitidos ficam no catálogo. Estados por
item: `cataloged`, `selected`, `processing`, `processed`, `failed`. Uma falha pode
ser tentada novamente; itens processados não são reenviados automaticamente.
Metodologias saem em `pending_review`, com fonte original e inferências
identificadas. Nenhuma transcrição integral é baixada, armazenada ou redistribuída.
Metadados expiram em 29 dias; a próxima utilização deve excluí-los/renová-los.

Pendência explícita: canal identificado por metadados oficiais, mas ID UC,
credencial Data API e autorização de conteúdo não foram fornecidos nesta sessão.
Não há conteúdo do canal indexado na entrega. Os métodos nativos são do Nexo,
não uma reprodução atribuída ao canal.

## Corpus canônico e administração do File Search — v2

Os [15 capítulos originais](knowledge/README.md) são carregados localmente sem
rede. Hash e caminho canônico identificam versões; anteriores são preservadas
como inativas. Recuperação local e remota ignoram versões registradas como
inativas. O índice remoto é reconstruível dos mesmos arquivos. Revisar um
capítulo como referência não o transforma em cálculo aprovado.

```powershell
& $ai -m nexo.infrastructure.intelligence.cli load-library
& $ai -m nexo.infrastructure.intelligence.cli list-stores
& $ai -m nexo.infrastructure.intelligence.cli create-store 'Nexo biblioteca v2'
# Substitua STORE_ID pelo nome retornado. Os comandos acima não fazem upload.
& $ai -m nexo.infrastructure.intelligence.cli --store fileSearchStores/STORE_ID sync-library --limit 3 --allow-paid-indexing
```

`--store` seleciona o índice para uma operação sem escrever `.env`. Para usá-lo
nas respostas, configure `NEXO_AI_FILE_SEARCH_STORE` e reinicie. Listagem tem
limite 20; sincronização 3 documentos por comando. Repita conscientemente lotes.
Hash indexado/operação pendente não é reenviado. Alteração cria nova versão.
Nenhuma operação remota ocorre ao abrir a UI. A chave por si só não autoriza
cobrança de embeddings. Recuperação e function calling ficam separados;
aceite autenticado da compatibilidade do modelo/store continua pendente.
Nenhum índice remoto foi criado nesta entrega.

Dois registros `reference_only` vêm do oEmbed oficial, sem conteúdo de vídeo:
7wOGP2bklNc e _CVsSXQ6NMc. Títulos/autoria/handle confirmados em 03/11/2026;
duração/publicação/ID UC continuam ausentes, sem inferência por título.
Para importar até 30 registros via Data API, incluindo sementes antigas:

```powershell
& $ai -m nexo.infrastructure.intelligence.cli catalog-youtube --confirmed-channel-id UC_ID_CONFIRMADO --limit 25 --video-id 7wOGP2bklNc --video-id _CVsSXQ6NMc
```

Sem `YOUTUBE_API_KEY`, essa operação não foi executada. O ID confirmado deve
corresponder ao handle. Metadados não autorizam processamento. Refresh preserva
permissão já registrada. Processamento exige referência escrita, identidade
confirmada e `--allow-cloud`, com contagem prévia de tokens.
