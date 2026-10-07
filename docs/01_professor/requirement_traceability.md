# Rastreabilidade dos requisitos acadêmicos

## Convenções

- **Definido:** decisão documental, sem implementação.
- **Estruturado:** diretórios/arquivos preparados, sem comportamento.
- **Em implementação:** código parcial verificável.
- **Implementado:** comportamento existente, ainda não necessariamente testado.
- **Testado:** evidência automatizada ou roteiro validado.
- **Pendente de confirmação:** depende do professor ou registro externo.

Fonte oficial: `original_requirements/REQUISITOS PROJETO SEMESTRAL.pdf`.
Menção em Markdown não é evidência de implementação.

## Matriz

| ID | Obrigação | Evidência atual ou esperada | Status |
|---|---|---|---|
| A-001 | Desenvolvimento individual | Declaração e histórico do repositório | Pendente de confirmação |
| A-002 | Proposta aprovada | Proposta e aprovação datadas | Pendente de confirmação |
| A-003 | Tema não substituído sem autorização | Comparação entre proposta e entrega | Pendente de confirmação |
| A-004 | Autor compreende e explica | Apresentação e arguição | Não iniciado |
| A-005 | Python 3.x | Aplicação executada no Windows com Python 3.14.0 | Testado |
| A-006 | POO efetiva | Portfolio/Transaction persistidos, posições derivadas e UI financeira | Testado no incremento 03 |
| A-007 | Classes, atributos, métodos e encapsulamento | Modelos imutáveis e regras financeiras; testes de Domain, Application, banco e UI | Testado no incremento 03 |
| A-008 | Associação e composição na redação oficial | Composição definida; orientação posterior rejeita associação no modelo atual | Pendente de confirmação |
| A-009 | Herança quando pertinente | Widgets/diálogos Qt e implementação da ABC PortfolioRepository; sem subclasses financeiras artificiais | Implementado |
| A-010 | Polimorfismo quando pertinente | Application usa PortfolioRepository SQLAlchemy ou fake nos testes | Testado |
| A-011 | Responsabilidades e modularização | main.py compõe UI, Application, Domain e Infrastructure | Implementado no incremento 01 |
| A-012 | GUI funcional no Windows | Carteiras e registro/consulta BUY/SELL, posições e troca por ID verificados com pytest-qt | Testado no incremento 03 |
| A-013 | Interface organizada e usável | Tema/componentes e estado vazio reais; revisão de DPI pendente | Em implementação |
| A-014 | Elemento gráfico funcional | QtCharts: fechamento real de ativo e custo versus valor das posições | Testado no incremento 04 |
| A-015 | Ao menos uma integração válida | SQLite armazena/consulta carteiras criadas pela interface | Testado |
| A-016 | Banco com finalidade prática | Portfolio e Transaction persistem após reabertura; FK/Decimal/datetime validados | Testado no incremento 03 |
| A-017 | API/web processa dados | brapi v2: quotes/busca/histórico mapeados e usados em valuation/GUI | Testado no incremento 04 |
| A-018 | Proposta com conteúdo exigido | Artefato/aprovação não confirmados | Pendente de confirmação |
| A-019 | Versão funcional na parcial | Fluxo de carteiras disponível; apresentação não registrada | Pendente de confirmação |
| A-020 | Conteúdo da parcial | Material não localizado | Não iniciado |
| A-021 | Demonstração funcional final | Fluxo financeiro funcional disponível; apresentação pendente | Em implementação |
| A-022 | Respostas técnicas na final | Código e documentação disponíveis; ensaio pendente | Não iniciado |
| A-023 | Datas acadêmicas | 26/08, 30/09 e 04/11; ano ausente no PDF | Pendente de confirmação |

## Cobertura honesta de POO

| Conceito | Situação |
|---|---|
| Classes/objetos | Portfolio, Asset, Transaction, Position, TransactionType, casos de uso, repository e UI implementados. |
| Atributos/métodos | Portfolio.id/name e operações execute/add/list_all. |
| Encapsulamento | Modelos frozen/slots normalizam e validam dados; invariantes financeiras testadas. |
| Composição | Transaction/Position contêm Asset; resultado contém snapshots; MainWindow recebe casos de uso. |
| Herança | Implementação de ABC e especialização Qt; sem hierarquia de ativos. |
| Polimorfismo | Mesma Application opera com repositories e MarketDataProvider real/fake. |
| Abstração | PortfolioRepository define somente add/list_all. |
| Responsabilidade única/modularização | Fluxo real separado por camadas; ORM restrito à Infrastructure. |

## Confirmações pendentes

1. Evidência, data e conteúdo da proposta aprovada.
2. Ano correspondente às datas do cronograma.
3. Como conciliar a redação oficial de A-008 com a orientação posterior do
   professor de que associação não se aplica ao modelo.
4. Obrigatoriedade de relatório, manuais ou slides como artefatos separados.

## Evidência histórica funcional do incremento 02

| Requisito | Evidência | Limite |
|---|---|---|
| RF-002 | Transaction valida compra/venda, ativo, quantidade, preço, taxas e datetime | Em memória; registro pela UI pendente |
| RF-003 | Portfolio já persiste | Ledger Transaction ainda não persiste |
| RF-004 | rebuild_positions reconstrói quantidade, média e custo | Testado diretamente no domínio |
| RF-005 | InsufficientPositionError rejeita venda sem saldo | Gravação atômica depende do futuro ledger |
| RF-006 | Isolamento por portfolio_id + Asset | Consultas pela UI pendentes |
| RNF-002 / RNF-004 | Domain usa biblioteca padrão e Decimal finito | Sem ORM, SQLite, PySide6 ou HTTP nos módulos novos |
| RNF-007 | 116 testes novos de domínio, incluindo invariantes e determinismo | Sem dependências novas |

Asset demonstra value object; Transaction/Portfolio demonstram entidades;
TransactionType demonstra Enum. Transaction referencia Portfolio por identidade,
sem ORM. Reconstrução abstrai comportamento financeiro sem hierarquia artificial.
Essas evidências não resolvem a confirmação acadêmica de A-008, ainda pendente.

## Evidência atual — Grande Incremento 03

A matriz e a evidência 02 acima registram estágios anteriores. Atualização atual:

| Requisito | Evidência implementada/testada | Limite |
|---|---|---|
| RF-002 | UI registra BUY/SELL via RegisterTransaction | Operações simuladas |
| RF-003 / RF-010 | SQLite persiste Portfolio e Transaction | CREATE/READ de transações |
| RF-004 | Posições e média reconstruídas após reinício | Sem dados de mercado |
| RF-005 | Replay integral rejeita saldo insuficiente antes do INSERT | Uma instância escritora |
| RF-006 | Histórico e posições mudam pela seleção de carteira por ID | Filtros em memória |
| RF-008 | Métricas reais na Visão Geral | Gráficos financeiros reais ainda pendentes |
| RNF-002 / RNF-003 | Domain/Application sem ORM; UI sem SQL/HTTP | Infrastructure mantém SQLAlchemy |
| RNF-004 / RNF-007 | Decimal TEXT round-trip e testes financeiros | Formatação visual em duas casas |
| A-006 / A-007 | Modelos imutáveis, contratos, casos de uso e regras encapsuladas | Autor ainda deve explicar na arguição |
| A-012 / A-015 / A-016 | UI financeira grava/lê SQLite e reabre em outra janela | Validado por pytest-qt |
| A-014 | Gráficos demonstrativos separados de métricas reais | Requisito gráfico funcional ainda parcial |

Não há subclasses artificiais ou fonte financeira duplicada em Position.
Confirmações acadêmicas de A-008, aprovação e calendário continuam pendentes.


## Evidência atual — Grande Incremento 04

As evidências 02/03 são históricas; o estado atual amplia a integração.

| Requisito | Evidência verificada | Limite |
|---|---|---|
| RF-007 / A-017 | brapi v2 com httpx; cotação/busca/histórico reais e smoke online | Cobertura B3/plano |
| RF-008 / A-014 | KPIs reais, gráfico de custo versus valor aberto e fechamento de ativo | Evolução histórica/benchmarks ainda demo |
| RF-101 | Valuation Decimal: aberto, não realizado, total e retorno sobre custo aberto | Sem caixa/FX/retorno total percentual |
| RF-103 | Fonte, moeda, referência/consulta e disponibilidade na GUI | Cotação não garante tempo real |
| RNF-002/003/006 | Contrato independente; HTTP só Infrastructure, regras em calculations | main.py compõe concretos |
| RNF-004/005/007 | Decimal JSON direto, token externo seguro, testes MockTransport/fake/Qt | Suíte sem internet |
| A-010 | Mesmos casos de uso funcionam com fake e BrapiMarketDataProvider | Sem abstrações artificiais |
| A-012/015 | UI/SQLite/HTTP controlado, reabertura e novos preços sem persistência de quote | Revisão DPI prolongada pendente |

77 testes novos e 245 anteriores preservados. Requisitos acadêmicos pendentes
(A-008, proposta, calendário e arguição) não são considerados atendidos por API.

## Evidência atual — Grande Incremento 05

As seções 02–04 são históricas. Evidência atual, sem presumir aprovação acadêmica:

| Requisito | Evidência | Limite |
|---|---|---|
| RF-007 / A-017 | Fundamentos/proventos brapi v2 por FundamentalDataProvider | B3/BRL/plano; falhas nullable |
| RF-006 / RF-008 | Comparação de duas ou mais carteiras por ID, métricas e concentração | Foto atual, sem performance temporal |
| RF-101 / A-014 | Graham/Bazin/margem e gráficos reais de valor/concentração | Yield explícito; sem recomendação |
| RF-103 | Fórmula/origem/moeda/referência/consulta e razões visíveis | Referência pode faltar |
| RNF-002/003/006 | UI recebe DTOs; HTTP/cache só infraestrutura; calculations puras | Schema mantém só portfolios/transactions |
| RNF-004/007 | Decimal, testes controlados, Qt heartbeat/gerações, TTL/refresh | Suíte sem internet |
| A-006/007/010 | Imutabilidade, composição e dois contratos com mesmo adapter/fake | Sem herança artificial de Asset |

Os 322 testes anteriores permanecem intactos; suíte analytics adicionada. Fórmulas
em [ANALYTICS.md](../02_architecture/ANALYTICS.md), resultados de verificação em
[TESTING.md](../04_development/TESTING.md). A-008/proposta/calendário ainda pendentes.
