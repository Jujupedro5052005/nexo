# Requisitos do Nexo Invest

## Convenções

- **MUST:** necessário para o núcleo funcional ou para a obrigação acadêmica.
- **SHOULD:** importante para a qualidade e a proposta, mas pode ser entregue
  depois do primeiro fluxo completo.
- **COULD:** complementar; não bloqueia o núcleo.

A fonte normativa acadêmica é
`docs/01_professor/original_requirements/REQUISITOS PROJETO SEMESTRAL.pdf`.
Em divergências, ela e orientações posteriores confirmadas pelo professor
prevalecem sobre decisões internas.

## Requisitos funcionais

### MUST

| ID | Requisito |
|---|---|
| RF-001 | Criar, identificar, nomear, selecionar e manter múltiplas carteiras simuladas. |
| RF-002 | Registrar compras e vendas por carteira com ativo, tipo, quantidade, preço e data. |
| RF-003 | Persistir dados estruturais de `Portfolio` e o ledger de `Transaction`. |
| RF-004 | Reconstruir `Position`, quantidade, preço médio e valor investido das transações. |
| RF-005 | Impedir venda acima da quantidade disponível sem gravação parcial. |
| RF-006 | Consultar histórico e posições separadamente por carteira. |
| RF-007 | Consultar ativos e dados de mercado por integração isolada da UI. |
| RF-008 | Exibir dashboard e gráficos funcionais baseados nos dados da carteira. |
| RF-009 | Comparar duas ou mais carteiras por métricas documentadas. |
| RF-010 | Persistir dados localmente em SQLite por Infrastructure. |

### SHOULD

| ID | Requisito |
|---|---|
| RF-101 | Calcular valor atual, lucro/prejuízo e rentabilidade quando houver cotação. |
| RF-102 | Disponibilizar indicadores e análises priorizados. |
| RF-103 | Exibir origem, horário e estado de disponibilidade de dados externos. |
| RF-104 | Configurar e exibir alertas de preço dentro da aplicação. |
| RF-105 | Oferecer validações, estados vazios e mensagens compreensíveis. |

### COULD

| ID | Requisito |
|---|---|
| RF-201 | Adicionar planejamento e educação financeira. |
| RF-202 | Adicionar notificações externas. |
| RF-203 | Adicionar IA e integrações adicionais. |
| RF-204 | Ampliar projeções, risco e valuation. |

## Requisitos não funcionais

| ID | Prioridade | Requisito |
|---|---|---|
| RNF-001 | MUST | Aplicação desktop executável no Windows com PySide6. |
| RNF-002 | MUST | Domain independente de PySide6, SQLAlchemy, SQLite e HTTP. |
| RNF-003 | MUST | UI sem SQL, ORM, HTTP direto ou regras financeiras. |
| RNF-004 | MUST | Valores monetários representados por `Decimal` nas regras. |
| RNF-005 | MUST | Segredos somente por configuração externa e nunca versionados. |
| RNF-006 | MUST | Responsabilidades separadas entre UI, Application, Domain, Calculations e Infrastructure. |
| RNF-007 | SHOULD | Domínio e cálculos fortemente testados; banco e integrações com testes próprios. |
| RNF-008 | SHOULD | Falhas externas não devem bloquear ou expor detalhes técnicos na UI. |
| RNF-009 | SHOULD | Código e documentação devem permitir ao autor explicar as decisões adotadas. |

## Requisitos acadêmicos

| ID | Classificação | Requisito verificável |
|---|---|---|
| A-001 | Obrigatório | Desenvolvimento individual. |
| A-002 | Obrigatório | Proposta aprovada antes do desenvolvimento. |
| A-003 | Obrigatório | Não substituir o tema sem autorização. |
| A-004 | Obrigatório | Compreender e explicar código, estrutura, classes, métodos, bibliotecas, algoritmos e decisões. |
| A-005 | Obrigatório | Usar Python 3.x como linguagem principal. |
| A-006 | Obrigatório | Usar POO efetivamente, não apenas classes formais. |
| A-007 | Obrigatório | Demonstrar classes/objetos, atributos/métodos e encapsulamento. |
| A-008 | Obrigatório no documento oficial | O PDF enumera associação e composição. Orientação posterior registrada indica que associação não é adequada ao modelo atual; confirmar com o professor como evidenciar A-008 sem introduzir relação artificial. |
| A-009 | Condicional | Empregar herança somente quando pertinente. |
| A-010 | Condicional | Empregar polimorfismo somente quando pertinente. |
| A-011 | Obrigatório | Separar responsabilidades e modularizar o código. |
| A-012 | Obrigatório | Possuir GUI funcional executável no Windows. |
| A-013 | Obrigatório | Manter interface organizada, usável, clara e estética. |
| A-014 | Obrigatório | Exibir elemento gráfico/multimídia funcional, não apenas decorativo. |
| A-015 | Obrigatório | Implementar ao menos banco, hardware ou serviço/API/web como integração prática. |
| A-016 | Condicional | Se banco for escolhido, armazenar e consultar dados com finalidade prática. |
| A-017 | Condicional | Se API/web for escolhida, consumir e processar dados; abrir página não basta. |
| A-018 | Obrigatório | Proposta com título, problema, objetivo, funcionalidades, tecnologias, POO, integração, elemento gráfico e resultados. |
| A-019 | Obrigatório | Apresentação parcial com versão funcional, ainda que incompleta. |
| A-020 | Obrigatório | Parcial cobre escopo, arquitetura, classes, UI, funções, integração, dificuldades, pendências e plano. |
| A-021 | Obrigatório | Final demonstra software e funções principais. |
| A-022 | Obrigatório | Autor responde sobre arquitetura, POO, classes, integração, tecnologias, dificuldades, decisões e limitações. |
| A-023 | Obrigatório | Datas informadas no PDF: 26/08, 30/09 e 04/11; ano precisa de confirmação. |

## Aplicação de POO

- encapsulamento protege invariantes de modelos e operações;
- composição descreve o estado reconstruído do `Portfolio` e objetos contidos;
- abstração aparece em modelos focados e contratos necessários;
- polimorfismo pode aparecer em provedores ou repositórios intercambiáveis;
- herança não será criada artificialmente e ainda não está implementada;
- responsabilidade única orienta módulos e classes.

A menção documental não comprova implementação. O status de cada requisito e
as evidências reais ficam em
[`requirement_traceability.md`](../01_professor/requirement_traceability.md).

## Limites

PySide6, SQLite e uma API de mercado são decisões do Nexo, embora o documento
acadêmico apresente tecnologias como alternativas. O sistema não realiza
operações financeiras reais. Recursos COULD não devem ser promovidos a
obrigatórios sem revisão de escopo.

Permanecem pendentes: registro da proposta aprovada, ano do cronograma,
tratamento acadêmico final de A-008 e confirmação de artefatos finais não
enumerados claramente na fonte oficial.
