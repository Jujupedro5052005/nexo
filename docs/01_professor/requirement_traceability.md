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
| A-006 | POO efetiva | Portfolio, casos de uso, contrato e implementação SQLAlchemy no fluxo real | Testado no incremento 01 |
| A-007 | Classes, atributos, métodos e encapsulamento | Portfolio imutável valida nome/ID; testes em unit/domain | Testado no incremento 01 |
| A-008 | Associação e composição na redação oficial | Composição definida; orientação posterior rejeita associação no modelo atual | Pendente de confirmação |
| A-009 | Herança quando pertinente | Widgets/diálogos Qt e implementação da ABC PortfolioRepository; sem subclasses financeiras artificiais | Implementado |
| A-010 | Polimorfismo quando pertinente | Application usa PortfolioRepository SQLAlchemy ou fake nos testes | Testado |
| A-011 | Responsabilidades e modularização | main.py compõe UI, Application, Domain e Infrastructure | Implementado no incremento 01 |
| A-012 | GUI funcional no Windows | Criar/listar/selecionar carteiras verificado com pytest-qt e processos offscreen | Testado no incremento 01 |
| A-013 | Interface organizada e usável | Tema/componentes e estado vazio reais; revisão de DPI pendente | Em implementação |
| A-014 | Elemento gráfico funcional | QtCharts com dados demo, sem representar ledger real | Em implementação |
| A-015 | Ao menos uma integração válida | SQLite armazena/consulta carteiras criadas pela interface | Testado |
| A-016 | Banco com finalidade prática | Portfolio persiste após reabertura; Transaction planejada | Testado no incremento 01 |
| A-017 | API/web processa dados | Contrato/adaptador previstos; provedor indefinido | Planejado |
| A-018 | Proposta com conteúdo exigido | Artefato/aprovação não confirmados | Pendente de confirmação |
| A-019 | Versão funcional na parcial | Fluxo de carteiras disponível; apresentação não registrada | Pendente de confirmação |
| A-020 | Conteúdo da parcial | Material não localizado | Não iniciado |
| A-021 | Demonstração funcional final | Primeiro fluxo funcional disponível; funções financeiras e apresentação pendentes | Em implementação |
| A-022 | Respostas técnicas na final | Documentação existe; ensaio e código pendentes | Não iniciado |
| A-023 | Datas acadêmicas | 26/08, 30/09 e 04/11; ano ausente no PDF | Pendente de confirmação |

## Cobertura honesta de POO

| Conceito | Situação |
|---|---|
| Classes/objetos | Portfolio, casos de uso, repository e UI implementados. |
| Atributos/métodos | Portfolio.id/name e operações execute/add/list_all. |
| Encapsulamento | Portfolio normaliza/valida dados e impede alteração direta. |
| Composição | MainWindow recebe casos de uso prontos; cada caso recebe repository. |
| Herança | Implementação de ABC e especialização Qt; sem hierarquia de ativos. |
| Polimorfismo | Mesma Application opera com repository SQLAlchemy ou fake. |
| Abstração | PortfolioRepository define somente add/list_all. |
| Responsabilidade única/modularização | Fluxo real separado por camadas; ORM restrito à Infrastructure. |

## Confirmações pendentes

1. Evidência, data e conteúdo da proposta aprovada.
2. Ano correspondente às datas do cronograma.
3. Como conciliar a redação oficial de A-008 com a orientação posterior do
   professor de que associação não se aplica ao modelo.
4. Obrigatoriedade de relatório, manuais ou slides como artefatos separados.
