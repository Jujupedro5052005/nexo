# Requisitos do projeto Nexo

## 1. Critérios e fontes

Este documento registra os requisitos acadêmicos aplicáveis ao Nexo sem
transformar recomendações, exemplos ou exercícios de aula em obrigações.

- **Obrigatório**: a fonte oficial usa “deverá”, “deverão”, “é obrigatório” ou
  define uma entrega, etapa ou data.
- **Obrigatório condicional**: aplica-se somente quando uma alternativa é
  escolhida ou quando o conceito é pertinente à modelagem.
- **Recomendação/critério**: descreve o nível esperado, boa prática ou aspecto
  avaliado, mas não integra sozinho o nível mínimo.
- **Exemplo**: tecnologia, funcionalidade, estrutura ou exercício ilustrativo.

A fonte normativa é `docs/01_professor/original_requirements/REQUISITOS
PROJETO SEMESTRAL.pdf`. Em divergências, ela prevalece sobre os materiais de
aula e as decisões internas.

## 2. Requisitos acadêmicos obrigatórios

### 2.1 Processo e autoria

| ID | Classificação | Requisito verificável | Origem |
|---|---|---|---|
| A-001 | Obrigatório | O projeto deve ser desenvolvido individualmente pelo aluno. | *REQUISITOS PROJETO SEMESTRAL*, p. 1, Introdução. |
| A-002 | Obrigatório | Apresentar uma proposta e somente iniciar o desenvolvimento após aprovação do professor. | *REQUISITOS PROJETO SEMESTRAL*, p. 1, Introdução. |
| A-003 | Obrigatório | Não substituir o tema aprovado, salvo situação excepcional autorizada pelo professor. | *REQUISITOS PROJETO SEMESTRAL*, p. 1, Introdução. |
| A-004 | Obrigatório | Compreender e conseguir explicar código, estrutura, funcionamento, classes, métodos, bibliotecas, algoritmos e decisões. | *REQUISITOS PROJETO SEMESTRAL*, p. 6, Uso de IA Generativa. |

### 2.2 Tecnologia, POO e arquitetura

| ID | Classificação | Requisito verificável | Origem |
|---|---|---|---|
| A-005 | Obrigatório | Usar Python 3.x como linguagem principal. | *REQUISITOS PROJETO SEMESTRAL*, p. 2, Linguagem Python e POO. |
| A-006 | Obrigatório | Usar POO efetivamente na arquitetura e organização; apenas criar classes formalmente não basta. | *REQUISITOS PROJETO SEMESTRAL*, p. 2, Linguagem Python e POO. |
| A-007 | Obrigatório | Demonstrar classes e objetos, atributos e métodos e encapsulamento. | *REQUISITOS PROJETO SEMESTRAL*, p. 2, Linguagem Python e POO. |
| A-008 | Obrigatório | Demonstrar associação e composição de objetos. | *REQUISITOS PROJETO SEMESTRAL*, p. 2, Linguagem Python e POO. |
| A-009 | Obrigatório condicional | Empregar herança quando pertinente, sem criar hierarquia artificial. | *REQUISITOS PROJETO SEMESTRAL*, p. 2; *Aula - Classes e Objetos - Herança*, pp. 2 e 11-16. |
| A-010 | Obrigatório condicional | Empregar polimorfismo quando pertinente à modelagem. | *REQUISITOS PROJETO SEMESTRAL*, p. 2; *Aula - Classes e Objetos - Introdução*, pp. 5, 8 e 11. |
| A-011 | Obrigatório | Separar responsabilidades entre classes e organizar/modularizar o código. | *REQUISITOS PROJETO SEMESTRAL*, p. 2, Linguagem Python e POO. |

### 2.3 Interface e recursos visuais

| ID | Classificação | Requisito verificável | Origem |
|---|---|---|---|
| A-012 | Obrigatório | Possuir interface gráfica funcional executável no Windows. | *REQUISITOS PROJETO SEMESTRAL*, p. 2, Interface gráfica. |
| A-013 | Obrigatório | Tratar a interface como parte integrante do software, com organização, usabilidade, clareza e estética. | *REQUISITOS PROJETO SEMESTRAL*, p. 3, Interface gráfica. |
| A-014 | Obrigatório | Manipular, gerar ou exibir funcionalmente elemento gráfico/multimídia relacionado à proposta; decoração isolada não basta. | *REQUISITOS PROJETO SEMESTRAL*, p. 3, Elementos gráficos ou multimídia. |

### 2.4 Integração

| ID | Classificação | Requisito verificável | Origem |
|---|---|---|---|
| A-015 | Obrigatório | Implementar ao menos uma opção: banco de dados; hardware externo; ou serviço externo/API/recurso web. | *REQUISITOS PROJETO SEMESTRAL*, pp. 3-4, Integração. |
| A-016 | Obrigatório condicional | Se banco for escolhido, usá-lo com finalidade prática, como armazenar, consultar, editar ou gerenciar informações. | *REQUISITOS PROJETO SEMESTRAL*, pp. 3-4, Opção A. |
| A-017 | Obrigatório condicional | Se serviço/API/web for escolhido, trocar, consumir, processar ou enviar informações; abrir uma página não basta. | *REQUISITOS PROJETO SEMESTRAL*, pp. 4-5, Opção C. |

### 2.5 Proposta e apresentações

| ID | Classificação | Requisito verificável | Origem |
|---|---|---|---|
| A-018 | Obrigatório | A proposta deve conter título; problema/ideia; objetivo; funcionalidades; tecnologias/bibliotecas; uso de POO; integração; elementos gráficos/multimídia; e resultados esperados. | *REQUISITOS PROJETO SEMESTRAL*, p. 6, Proposta. |
| A-019 | Obrigatório | Na apresentação parcial deve existir versão funcional, ainda que incompleta; slides, protótipos ou descrição isolados não bastam. | *REQUISITOS PROJETO SEMESTRAL*, pp. 6-7, Apresentação parcial. |
| A-020 | Obrigatório | Na parcial, apresentar objetivo/escopo, arquitetura inicial, classes, interface funcionando, funcionalidades, integração/estágio, dificuldades, pendências e plano de conclusão. | *REQUISITOS PROJETO SEMESTRAL*, p. 7, Apresentação parcial. |
| A-021 | Obrigatório | Na final, demonstrar o software funcionando, funcionalidades principais e decisões adotadas. | *REQUISITOS PROJETO SEMESTRAL*, p. 7, Apresentação final. |
| A-022 | Obrigatório | Na final, responder sobre arquitetura, POO, classes, integração, tecnologias, dificuldades, decisões, limitações e melhorias. | *REQUISITOS PROJETO SEMESTRAL*, p. 7, Apresentação final. |
| A-023 | Obrigatório | Cumprir: proposta 26/08, parcial 30/09 e final 04/11. O PDF não informa o ano, que deve ser confirmado. | *REQUISITOS PROJETO SEMESTRAL*, p. 9, Cronograma. |

## 3. Recomendações e critérios de avaliação

| ID | Classificação | Orientação | Origem |
|---|---|---|---|
| Q-001 | Nível esperado | Boa organização OO, interface adequada, múltiplas funcionalidades relacionadas, tratamento de erros, validação e integração consistente. | *REQUISITOS PROJETO SEMESTRAL*, p. 5, Níveis. |
| Q-002 | Critério | Priorizar solução funcional, bem estruturada, coerente e compreendida; quantidade de funcionalidades isolada não aumenta a nota. | *REQUISITOS PROJETO SEMESTRAL*, pp. 1, 8-10. |
| Q-003 | Critério | Avaliam-se POO/arquitetura, funcionalidade, complexidade, código, interface/experiência, integração, apresentação e domínio. | *REQUISITOS PROJETO SEMESTRAL*, p. 8, Avaliação. |
| Q-004 | Regra de avaliação | Avaliação: 60% professor e 40% média dos colegas. | *REQUISITOS PROJETO SEMESTRAL*, p. 8, Avaliação. |
| Q-005 | Recomendação | Preferir documentação oficial das tecnologias utilizadas. | *REQUISITOS PROJETO SEMESTRAL*, pp. 8-9, Fontes. |
| Q-006 | Recomendação | Definir escopo viável; evitar simplicidade excessiva e complexidade incompatível com o prazo. | *REQUISITOS PROJETO SEMESTRAL*, pp. 1 e 9-10. |

## 4. Conceitos de POO a evidenciar

Exigidos explicitamente: classes e objetos; atributos e métodos;
encapsulamento; associação e composição; separação de responsabilidades;
organização e modularização; herança e polimorfismo quando pertinentes. Fonte:
*REQUISITOS PROJETO SEMESTRAL*, p. 2.

Fundamentação dos materiais:

- **Abstração** é um dos quatro pilares ensinados, mas não foi enumerada
  isoladamente no mínimo oficial (*Introdução*, pp. 8-9).
- **Encapsulamento** protege estado e controla alterações (*Encapsulamento*,
  pp. 2-4 e 7-9).
- **Herança** exige relação “é um”; relação “tem um” pede composição
  (*Herança*, pp. 2 e 11-16).
- **Polimorfismo** permite respostas distintas à mesma operação
  (*Introdução*, pp. 5 e 11).
- **Métodos dunder** são conteúdo didático, não requisito semestral (*Métodos
  Dunder*, pp. 2-10).
- **UML** é ferramenta de modelagem apresentada em aula, não entrega
  obrigatória (*Introdução*, pp. 18-20).

## 5. Exemplos que não são requisitos do Nexo

- PySide6, PyQt6, Tkinter, CustomTkinter, Flet e Pygame são exemplos permitidos,
  não imposições (*REQUISITOS PROJETO SEMESTRAL*, p. 2).
- Imagens, gráficos, mapas, dashboards, sprites e vídeos são alternativas; não
  é preciso implementar todos (*REQUISITOS PROJETO SEMESTRAL*, p. 3).
- SQLite, MySQL, PostgreSQL, MongoDB e Firebase são exemplos; vale a finalidade
  prática da integração (*REQUISITOS PROJETO SEMESTRAL*, pp. 3-4).
- IA, visão computacional, tempo real, múltiplas integrações e dashboards
  avançados são diferenciais (*REQUISITOS PROJETO SEMESTRAL*, p. 5).
- Calculadora, Pokémon, Temperatura, gestão universitária, biblioteca, forca e
  encriptador são exercícios das respectivas aulas, não funcionalidades do Nexo
  (*Calculadora*, pp. 2-8; *Introdução*, pp. 21-22; *Encapsulamento*, pp. 11-12;
  *Herança*, pp. 17-23; *Métodos Dunder*, pp. 11-15; *Aula 03*, pp. 5-6;
  *Aula 04*, pp. 6-9).
- Funções, módulos, `math`, `cmath`, strings, listas e dicionários são conteúdos
  introdutórios, não requisitos (*Aula 02*, pp. 2-5; *Aula 03*, pp. 2-4;
  *Aula 04*, pp. 2-5).

## 6. Decisões próprias do Nexo

Estes itens são internos e devem ser validados contra a proposta aprovada.

| ID | Estado | Decisão | Origem interna |
|---|---|---|---|
| N-001 | Definido | Aplicação desktop de investimentos e planejamento financeiro. | `README.md`; `PROJECT_OVERVIEW.md`. |
| N-002 | Definido | Carteiras simuladas; não executar ordens reais. | `PROJECT_OVERVIEW.md`. |
| N-003 | Previsto | PySide6 para interface. | `README.md`; `requirements.txt`; `UI_ARCHITECTURE.md`. |
| N-004 | Previsto | SQLite e SQLAlchemy para persistência. | `README.md`; `requirements.txt`; `DATABASE.md`. |
| N-005 | Previsto | APIs externas de dados financeiros. | `README.md`; `requirements.txt`; `API_ARCHITECTURE.md`. |
| N-006 | Previsto | Separar UI, aplicação, domínio e infraestrutura. | `AGENTS.md`; `ARCHITECTURE.md`. |
| N-007 | Em definição | Mercado, Carteira, Análises, Alertas, Planejamento e Educação financeira. | `PROJECT_OVERVIEW.md`; `ROADMAP.md`. |

## 7. Conflitos, riscos e lacunas

Não há conflito técnico inevitável entre o Nexo e os requisitos. Há estes
pontos a resolver:

| ID | Situação | Impacto | Ação recomendada |
|---|---|---|---|
| C-001 | Não há registro da proposta nem da aprovação. | Sem evidência para A-002, A-003 e A-018. | Registrar proposta aprovada, data e ressalvas. |
| C-002 | `SCOPE.md` não define MVP e o roadmap lista seis módulos amplos. | Risco de escopo excessivo frente a Q-002/Q-006. | Fechar MVP e deixar módulos avançados para o futuro. |
| C-003 | O plano prevê banco e API. | Compatível, mas A-015 exige apenas uma; duas aumentam risco. | Definir integração mínima e diferencial na proposta. |
| C-004 | Dashboards/análises não têm aceite funcional definido. | Decoração não atende A-014. | Definir visualização alimentada por dados e útil ao usuário. |
| C-005 | Arquitetura e domínio ainda estão em TODO. | Sem evidência de A-006 a A-011. | Mapear classes, relações e responsabilidades antes do código. |
| C-006 | Ainda não há interface funcional/vertical slice. | A-012, A-019 e A-021 não demonstráveis. | Planejar a primeira fatia funcional para a parcial. |
| C-007 | O cronograma não informa ano. | Risco de interpretar A-023 incorretamente. | Confirmar calendário com o professor; não inferir. |
| C-008 | Checklist interno pede relatório, manuais e slides finais. | Tais entregas não constam dos PDFs analisados. | Tratar como decisão interna ou confirmar com o professor. |
| C-009 | Ainda não existe domínio que justifique herança. | Forçar hierarquia contrariaria a pertinência de A-009. | Justificar semanticamente o uso ou a não aplicação. |

O status e as evidências estão em
`docs/01_professor/requirement_traceability.md`.
