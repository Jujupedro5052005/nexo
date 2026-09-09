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
- diálogos: título, campos, feedback demonstrativo e ações claras.

Os ícones são vetores desenhados com `QPainter` em `src/nexo/ui/icons.py`. Isso
mantém estilo uniforme sem imagens raster ou dependência adicional.

## Dados demonstrativos

O protótipo usa exclusivamente o dataset de apresentação em
`src/nexo/ui/demo/data.py`. Páginas que exibem esses valores mostram o badge
“Dados demonstrativos”. Esses dados não pertencem ao Domain, Application ou
Infrastructure e serão substituídos por resultados de casos de uso.

## Estados e interação

Controles interativos possuem hover, pressionado, selecionado ou desabilitado,
conforme aplicável. Ações ainda sem backend abrem um diálogo ou mostram uma
mensagem de que a conexão será feita posteriormente. Opções não disponíveis,
como tema claro e exportação local, permanecem desabilitadas ou marcadas “Em
breve”.

Gráficos atuais são widgets reais alimentados por dados demonstrativos. Eles não
comprovam a implementação de métricas financeiras nem atendem sozinhos ao
requisito de gráficos baseados em dados reais da carteira.
