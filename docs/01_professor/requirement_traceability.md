# Rastreabilidade dos requisitos acadêmicos

## Convenções

- Fonte oficial: `original_requirements/REQUISITOS PROJETO SEMESTRAL.pdf`.
- Os PDFs de `class_material/` explicam conceitos e trazem exercícios; não
  substituem o documento oficial.
- **Planejado** indica decisão registrada, ainda sem evidência funcional.
- **Pendente de confirmação** depende de registro externo ou do professor.

## Matriz de rastreabilidade

| ID | Obrigação | Fonte (seção/página) | Evidência/implementação prevista | Verificação de aceite | Status |
|---|---|---|---|---|---|
| A-001 | Desenvolvimento individual | *REQUISITOS PROJETO SEMESTRAL*, Introdução, p. 1 | Declaração de autoria e histórico do repositório | Conferência de autoria | Pendente de confirmação |
| A-002 | Proposta aprovada antes do desenvolvimento | Documento oficial, Introdução, p. 1 | Proposta aprovada e registro datado | Conferir aprovação e data | Pendente de confirmação |
| A-003 | Não substituir tema sem autorização | Documento oficial, Introdução, p. 1 | Tema aprovado e eventual autorização | Comparar proposta e entrega | Pendente de confirmação |
| A-004 | Autor compreender e explicar o código | Documento oficial, Uso de IA, p. 6 | Arquitetura, decisões e preparação da apresentação | Arguição sobre código e decisões | Não iniciado |
| A-005 | Python 3.x principal | Documento oficial, Linguagem Python e POO, p. 2 | `src/nexo/`, dependências e ambiente | Executar app/testes em versão registrada | Planejado |
| A-006 | POO efetiva na arquitetura | Documento oficial, Linguagem Python e POO, p. 2 | Camadas previstas; modelo pendente | Revisão arquitetural e colaboração entre objetos | Planejado |
| A-007 | Classes/objetos, atributos/métodos e encapsulamento | Documento oficial, p. 2; apoio: *Encapsulamento*, pp. 2-9 | Entidades e regras a definir | Testes de invariantes e acesso ao estado | Não iniciado |
| A-008 | Associação e composição | Documento oficial, p. 2; apoio: *Herança*, pp. 12-16 | Relações do domínio a definir | Revisão do modelo e testes de colaboração | Não iniciado |
| A-009 | Herança quando pertinente | Documento oficial, p. 2; apoio: *Herança*, pp. 2, 11-16 | Somente relação “é um” justificável | Revisão semântica/testes ou justificativa de não aplicação | Não iniciado |
| A-010 | Polimorfismo quando pertinente | Documento oficial, p. 2; apoio: *Introdução*, pp. 5, 8, 11 | Contratos e variações reais a definir | Consumidor comum com implementações distintas ou justificativa | Não iniciado |
| A-011 | Responsabilidades e modularização | Documento oficial, p. 2 | Estrutura UI/aplicação/domínio/infraestrutura | Revisão de dependências e testes por camada | Planejado |
| A-012 | GUI funcional no Windows | Documento oficial, Interface gráfica, p. 2 | PySide6 previsto; UI vazia | Iniciar e percorrer interface no Windows | Planejado |
| A-013 | Interface organizada, usável, clara e estética | Documento oficial, Interface gráfica, p. 3 | Design ainda em definição | Roteiro de usabilidade e revisão visual | Não iniciado |
| A-014 | Elemento visual/multimídia funcional | Documento oficial, Elementos gráficos, p. 3 | Dashboards/análises previstos | Visualização usa dados e cumpre objetivo, não decorativo | Planejado |
| A-015 | Ao menos uma integração válida | Documento oficial, Integração, pp. 3-4 | Banco e API previstos | Demonstração ponta a ponta de pelo menos uma opção | Planejado |
| A-016 | Banco, se escolhido, com finalidade prática | Documento oficial, Opção A, pp. 3-4 | SQLite/SQLAlchemy previstos | Criar, consultar e alterar dados do caso de uso | Planejado |
| A-017 | API/web, se escolhida, troca/processa dados | Documento oficial, Opção C, pp. 4-5 | `httpx` previsto; provedor indefinido | Teste de integração e dado processado na aplicação | Planejado |
| A-018 | Proposta com nove itens exigidos | Documento oficial, Proposta, p. 6 | Artefato não localizado | Checklist dos nove campos e aprovação | Pendente de confirmação |
| A-019 | Versão funcional na parcial | Documento oficial, Apresentação parcial, pp. 6-7 | Vertical slice pendente | Executar versão; protótipo/slides isolados não passam | Não iniciado |
| A-020 | Conteúdo completo da parcial | Documento oficial, Apresentação parcial, p. 7 | Material não localizado | Checklist dos nove tópicos | Não iniciado |
| A-021 | Demonstração funcional final | Documento oficial, Apresentação final, p. 7 | Demo pendente | Roteiro das funcionalidades principais | Não iniciado |
| A-022 | Respostas técnicas na final | Documento oficial, Apresentação final, p. 7 | Documentação/ensaio pendentes | Arguição simulada dos nove tópicos | Não iniciado |
| A-023 | Datas 26/08, 30/09 e 04/11 | Documento oficial, Cronograma, p. 9 | Ano não informado | Confirmação do calendário vigente | Pendente de confirmação |

## Cobertura de POO

| Conceito | Natureza | Fonte | Evidência esperada no Nexo |
|---|---|---|---|
| Classes/objetos | Obrigatório | Documento oficial, p. 2 | Entidades/serviços com responsabilidades coerentes |
| Atributos/métodos | Obrigatório | Documento oficial, p. 2 | Estado e comportamento relacionados nos objetos |
| Encapsulamento | Obrigatório | Documento oficial, p. 2; *Encapsulamento*, pp. 2-9 | Invariantes protegidas por operações do domínio |
| Associação | Obrigatório | Documento oficial, p. 2 | Relações explícitas entre objetos |
| Composição | Obrigatório | Documento oficial, p. 2; *Herança*, pp. 12-16 | Relações “tem um” sem herança indevida |
| Responsabilidade única/modularização | Obrigatório | Documento oficial, p. 2 | Camadas e módulos coesos |
| Herança | Condicional | Documento oficial, p. 2; *Herança*, pp. 2, 11-16 | Hierarquia “é um” ou justificativa de não pertinência |
| Polimorfismo | Condicional | Documento oficial, p. 2; *Introdução*, pp. 5, 11 | Contrato comum e respostas distintas ou justificativa |
| Abstração | Conteúdo didático | *Introdução*, pp. 8-9 | Modelos focados no essencial do domínio |
| Métodos dunder | Exemplo didático | *Métodos Dunder*, pp. 2-10 | Opcional; somente se trouxer semântica natural |
| UML | Ferramenta didática | *Introdução*, pp. 18-20 | Opcional para comunicar o modelo |

## Não promovidos a requisitos

- Calculadora, Pokémon, Temperatura, gestão universitária, biblioteca, forca e
  encriptador são exercícios de aula, não requisitos do projeto semestral.
- PySide6, SQLite, APIs REST e dashboards são alternativas/exemplos no
  documento oficial; são compromissos do Nexo apenas por decisão interna e
  pela proposta aprovada.
- Múltiplas integrações, IA, tempo real e dashboards avançados são
  diferenciais; o mínimo requer uma integração funcional.
- Relatório, manuais e slides finais constam do checklist interno, mas não foram
  encontrados como obrigações nos PDFs analisados.

## Confirmações pendentes do professor

1. Evidência e data de aprovação da proposta do Nexo.
2. Conteúdo e escopo exatos da proposta aprovada.
3. Ano correspondente às datas 26/08, 30/09 e 04/11.
4. Orientações posteriores não presentes nos arquivos analisados.
5. Obrigatoriedade de relatório, manuais ou slides como artefatos separados.
