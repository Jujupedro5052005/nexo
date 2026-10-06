# Design system do Nexo Invest

Este documento é a fonte de verdade visual. Ele não define regras de domínio,
persistência ou cálculos financeiros.

## Identidade

O Nexo usa uma interface escura, sóbria e contemporânea, inspirada em produtos
de análise financeira sem reproduzir a identidade de bancos existentes. O tema
prioriza leitura, densidade moderada, hierarquia clara e espaço entre blocos.

A implementação está centralizada em `src/nexo/ui/styles/theme.py`. Não devem
existir grandes folhas QSS duplicadas em páginas ou diálogos.

## Cores

| Papel | Cor |
|---|---|
| Fundo principal | `#050B16` |
| Sidebar | `#07111F` |
| Superfície | `#0C1727` |
| Superfície elevada | `#101D30` |
| Borda | `#243247` |
| Texto principal | `#F5F7FA` |
| Texto secundário | `#9AA7B8` |
| Destaque | `#10C7C7` |
| Positivo | `#3DDC84` |
| Negativo | `#FF5C6C` |
| Atenção | `#FFB020` |
| Informação | `#4D7CFF` |

Verde, vermelho e amarelo sempre aparecem acompanhados de texto, valor, estado
ou ícone. A cor não é o único meio de comunicar significado.

## Tipografia e espaçamento

A aplicação usa fontes disponíveis no sistema, na ordem Inter, Segoe UI,
Ubuntu e sans-serif. Títulos, subtítulos, KPIs, títulos de seção, labels e textos
secundários possuem níveis distintos. Cards usam cantos de 12 px, bordas
discretas, preenchimento interno entre 14 e 18 px e não usam sombras pesadas.

## Componentes

- `NavigationButton`: ícone vetorial, hover, pressionado e seleção ativa;
- `MetricCard`: título, valor, contexto, ícone e tooltip;
- `SectionCard`: contêiner compartilhado com ação opcional;
- `Badge`: identifica dados demonstrativos e estados;
- `DataTable`: tabela sem grade pesada e com seleção coerente com o tema;
- `PageContent`: conteúdo rolável, mantendo sidebar e topbar fixas;
- gráficos QtCharts: linha, barras e donut, sempre redimensionáveis;
- diálogos: título, campos e feedback; criação de carteira funcional, demais
  formulários demonstrativos, exceto compra/venda funcional.

Os ícones são vetores desenhados com `QPainter` em `src/nexo/ui/icons.py`. Isso
mantém estilo uniforme sem imagens raster ou dependência adicional.

## Dados demonstrativos

O protótipo usa o dataset em `src/nexo/ui/demo/data.py` e ainda possui
constantes inline nas páginas. Páginas com esses valores mostram o badge
“Dados demonstrativos”. Esses dados não pertencem ao Domain, Application ou
Infrastructure e serão substituídos por resultados de casos de uso.

Carteiras já usa entidades persistidas reais e exibe "Carteiras locais",
estado vazio e indicação de seleção por ID. Carteiras sem operações mostram
"Carteira vazia", "0 ativos" e "Sem movimentações", sem métricas fictícias.
A seleção combina botão checked e texto explícito.

## Estados e interação

Controles interativos possuem hover, pressionado, selecionado ou desabilitado,
conforme aplicável. Ações ainda sem backend abrem um diálogo ou mostram uma
mensagem de que a conexão será feita posteriormente. Opções não disponíveis,
como tema claro e exportação local, permanecem desabilitadas ou marcadas “Em
breve”.

Gráficos demonstrativos permanecem rotulados; gráficos de fechamento em Ativos
e custo versus valor em Visão Geral usam dados reais no incremento 04.

## Integração financeira — Grande Incremento 03

Carteiras mantém seleção por ID e adiciona posições e cards com capital alocado
a custo, realizado, número de ativos e movimentações. Carteira sem operações
mantém estado vazio real. Carteira encerrada pode ter histórico e resultado
realizado, mesmo sem posições abertas.

Movimentações utiliza histórico do SQLite, filtros de tipo/ativo/período e busca
por símbolo. Colunas incluem data/hora, BUY/SELL, ativo, quantidade, preço, taxas,
bruto e total/líquido. Não há ações enganosas de editar/excluir.
TransactionDialog tem somente BUY/SELL, carteira global, símbolo, quantidade,
preço, taxas e data/hora; aceita somente após commit e apresenta erros legíveis.

Visão Geral separa uma área real de métricas/posições de seções demonstrativas
identificadas individualmente. Custo de posições não é patrimônio de mercado;
cotações e valor de mercado são indisponíveis na área real. As demais páginas
mantêm seus badges demonstrativos. Valores monetários formatam duas casas apenas
na apresentação; quantidade preserva seus dígitos, sem converter para float.


## Mercado — Grande Incremento 04

Ativos substitui dados inline/demo por busca, cotação e gráfico real de fechamento.
Há estados buscando/carregando, vazio, sem acesso/limite/indisponível; falha limpa
valor/série anterior. Período da série é próprio (1M/3M/1A), separado do seletor
global ainda desabilitado. Fonte, moeda, horário de mercado e consulta aparecem
nos detalhes; ausência de horário não é ocultada.

Carteiras e Visão Geral acrescentam preço atual, valor, não realizado e retorno
aberto às posições. Cards de carteira incluem valor/não realizado/total; Overview
mantém KPIs locais e adiciona KPIs de mercado e barras reais de custo/valor das
posições BRL cotadas. Não chama esse valor de patrimônio total. Métricas faltantes
usam “—”, com motivo e tooltip por ativo; agregado incompleto nunca soma parcial.

Atualizar mercado (topbar) e Atualizar ativo são ações manuais reais. Novos botões
usam PrimaryButton/SecondaryButton; texto dos KPIs quebra linha para preservar
largura e tabela selecionada mantém contraste. Revisão de outras escalas pendente.

Evolução patrimonial, alocação por categoria, insights, caixa, metas e alertas
continuam abaixo da separação demo, com badges individuais. Um gráfico indisponível
na área real não recebe dataset demonstrativo como fallback.
