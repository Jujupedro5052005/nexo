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

Indexação opcional, somente após configurar um store existente e autorizar
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
3. Execute um lote pequeno; máximo de dez vídeos e três consultas de metadados
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
