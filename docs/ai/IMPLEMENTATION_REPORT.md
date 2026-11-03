# Relatório de implementação — 03/11/2026

Incremento real em `feature/nexo-intelligence`, com referência no commit
`2c04e0e`. O repositório remoto possui **master**, não main. A branch solicitada
foi criada sem modificar a branch-base.

Arquitetura: [ARCHITECTURE.md](ARCHITECTURE.md). Configuração e execução completas
para Windows/Linux: [GEMINI_SETUP.md](GEMINI_SETUP.md).

Funcional: página NEXO Intelligence com três abas; chat offline e adaptador
Gemini; histórico separado normal/demo; contexto de ativo/carteira; Markdown,
links, carregamento/erro/cancelamento; cards, sensibilidade e exportação Markdown;
ferramentas read-only reutilizando providers/cache; três valuations Decimal;
biblioteca textual autorizada; extração JSON e curadoria; File Search opcional;
catálogo YouTube pequeno por API oficial e análise de URL somente autorizada.

Arquivos principais criados:

- `domain/models/intelligence.py`, `domain/interfaces/intelligence.py`.
- `application/intelligence/`: contratos de ferramentas, orquestração, evidências,
  workspace, biblioteca nativa e revisão de conhecimento.
- `calculations/valuation/intelligence.py`.
- `infrastructure/intelligence/`: config, composição, SDK, SQLite, recuperação,
  catálogo e CLI de manutenção.
- `ui/pages/intelligence_page.py`, `ui/components/safe_markdown.py`.
- `tests/intelligence/` e os nove documentos de `docs/ai/`.

Arquivos existentes atualizados: composição em main.py, navegação/lifecycle da
MainWindow, expectativa de onze páginas no teste, dependência google-genai,
`.env.example`, README e documentação de escopo/requisitos/arquitetura/status.
Não houve alteração do `.env` do usuário ou dos bancos financeiros originais.

Integrações externas realmente verificadas nesta sessão:

- Consulta de branches no GitHub: remoto com `master`.
- Pesquisa na documentação oficial Google/Gemini/YouTube.
- Uma consulta pública oficial oEmbed confirmou nome e handle do canal.

Gemini geração, File Search, YouTube Data API e vídeo foram validados com mocks
e/ou transporte HTTP simulado pelo SDK real. **Não houve teste autenticado real**
dessas integrações: a chave não foi fornecida ao agente, o ID UC não foi
confirmado pela Data API e não há autorização do titular para processar vídeos.
Nenhum método entregue foi atribuído a vídeo não processado.

Consumo: nenhuma geração Gemini, nenhum token de inferência consumido por este
trabalho, nenhuma indexação paga nem mudança de faturamento. Pesquisa web,
instalação de dependências, Git e oEmbed não são inferência Gemini. Não foram
feitas novas consultas aos providers financeiros de produção.

Validação: suíte completa **764 aprovados, 2 ignorados**, zero falhas, em
376,84 s. Após os últimos ajustes de apresentação/ownership Qt e o limite de
precisão contra expoentes extremos, regressão final de IA: **77 aprovados,
2 ignorados**, em 5,75 s. Ruff check ., mypy src (**146 arquivos**), compileall
src/tests e git diff --check aprovados. Smokes reais continuam opt-in.
Um warning de depreciação interna do SDK no Python 3.14 é conhecido e não foi
suprimido artificialmente.

Limites: sem streaming; formulário de premissas com JSON avançado opcional;
cancelamento não desfaz request já
aceito; classificação de ativo manual; biblioteca local textual; sem corpus real
do canal; comparações de ativos por cotação (fundamentos podem ser consultados
separadamente); não há recomendação categórica, ordens, SQL/código livre, caixa
embutido na fotografia de posições ou conversão FX. Limite monetário remoto
não é garantido por contadores locais. O ID do projeto informado não prova que
a chave pertence a ele; confira no AI Studio.

Revisão visual: página capturada com Qt offscreen e fontes Windows, em SQLite
isolado, com valuation sintético conhecido. Corrigido overflow horizontal da
descrição de compartilhamento. Imagens/artefatos ficam em `tmp/intelligence_review/`
(ignorado). O teste de integração consulta posições e movimentações de um ledger
SQLite real temporário, preservando tabelas e contagem de transações.

Entrega preparada para PR contra master. Nenhuma mudança será mesclada
automaticamente. O link do PR é fornecido na resposta de entrega.
