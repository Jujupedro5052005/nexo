# Escopo acadêmico do Nexo

## 1. Objetivo do MVP

Entregar uma aplicação desktop para Windows, funcional e demonstrável, na qual
o usuário mantém uma carteira de investimentos exclusivamente simulada. O
núcleo permite registrar compras e vendas, consultar posições e preço médio,
revisar o histórico persistido e visualizar a alocação da carteira.

O recorte prioriza POO efetiva, interface clara, persistência prática em banco
de dados e visualização funcional. Ele atende primeiro aos requisitos A-005 a
A-016 e prepara as demonstrações A-019 a A-022. A API externa não é necessária
para considerar o CORE concluído; isso evita que rede, chave ou provedor
impeçam a apresentação.

## 2. Classificação das funcionalidades

| Funcionalidade imaginada | Classe | Justificativa |
|---|---|---|
| Carteira simulada | **CORE MVP** | É o agregado central do domínio e dá contexto coerente às demais operações. |
| Compra simulada | **CORE MVP** | Demonstra comportamento, validações, encapsulamento, persistência e atualização de posição. |
| Venda simulada | **CORE MVP** | Completa o fluxo da carteira e permite demonstrar regra de saldo/quantidade disponível. |
| Posição atual dos ativos | **CORE MVP** | É a consequência verificável das transações; no CORE significa quantidade e custo, sem cotação de mercado. |
| Cálculo de preço médio | **CORE MVP** | É uma regra de negócio central, testável e adequada à avaliação de POO. |
| Histórico de transações | **CORE MVP** | Torna a integração com banco prática e permite auditar o estado calculado. |
| Dashboard e gráficos | **CORE MVP** | Um dashboard mínimo de custo total e gráfico de alocação por custo atende ao elemento gráfico funcional A-014. |
| Consulta de ativos e cotações por API | **MVP EXTENDED** | Enriquece o produto e atende A-017, mas adiciona rede, chave, limites, adaptação e tratamento de indisponibilidade. O banco já atende A-015/A-016 no CORE. |
| Rentabilidade da carteira | **MVP EXTENDED** | Depende de cotações atuais confiáveis; será calculada após a integração de mercado. |
| Indicadores financeiros | **OPTIONAL** | É diferencial analítico, mas requer dados adicionais e não amplia de forma decisiva a demonstração mínima de POO. |
| Alertas configuráveis de preço | **OPTIONAL** | Depende de cotações e de mecanismo de avaliação; pode demonstrar polimorfismo, mas não é necessário para o mínimo. |
| Cálculos de valuation e preço teto | **FUTURE / OUT OF SCOPE** | Exigem premissas, dados fundamentalistas e validação financeira; aumentam muito o risco para pouco ganho acadêmico no MVP. |
| Notificações por e-mail ou WhatsApp | **FUTURE / OUT OF SCOPE** | Exigem credenciais, provedores e tratamento assíncrono; não são necessárias porque o banco já cobre integração. |
| Planejamento financeiro pessoal | **FUTURE / OUT OF SCOPE** | Abre um segundo domínio e dilui a coerência da entrega inicial. |
| Receitas e despesas | **FUTURE / OUT OF SCOPE** | Pertencem ao domínio de planejamento financeiro, sem dependência necessária com o núcleo da carteira. |
| Objetivos financeiros | **FUTURE / OUT OF SCOPE** | Dependem do módulo de planejamento e não contribuem para fechar o fluxo principal de investimentos. |
| Educação financeira | **FUTURE / OUT OF SCOPE** | Conteúdo estático acrescenta pouco à demonstração de regras, objetos e integração. |
| Possíveis integrações futuras | **FUTURE / OUT OF SCOPE** | Integrações sem caso de uso definido criam complexidade e não devem entrar na entrega inicial. |

## 3. CORE MVP aprovado

O CORE contém exatamente:

1. uma carteira simulada local;
2. cadastro implícito de um ativo pelo seu código durante a primeira transação;
3. registro de compra com ativo, quantidade, preço unitário e data;
4. registro de venda com validação da quantidade disponível;
5. posições derivadas das transações, com quantidade, preço médio e custo;
6. histórico persistido de compras e vendas;
7. dashboard com resumo de custo e gráfico de alocação por ativo;
8. interface PySide6 executável no Windows;
9. persistência SQLite por uma abstração de repositório;
10. validação de entradas e mensagens de erro compreensíveis.

Para conter o escopo, o CORE trabalha com uma única carteira local e não inclui
autenticação, múltiplos usuários, ordens reais, impostos, taxas, dividendos,
desdobramentos, renda fixa, moedas, sincronização ou edição retroativa de
transações. Uma correção pode ser feita removendo a transação e cadastrando-a
novamente somente se essa remoção for priorizada depois do fluxo básico.

## 4. Fluxos completos obrigatórios

### F-01 — Registrar compra e consultar posição

1. Abrir a aplicação e acessar a carteira.
2. Informar código do ativo, quantidade positiva, preço unitário positivo e
   data válida.
3. Confirmar a compra simulada.
4. Ver a transação no histórico.
5. Ver a posição criada/atualizada com quantidade, custo e preço médio corretos.
6. Fechar e reabrir a aplicação e encontrar os dados preservados.

### F-02 — Registrar nova compra e recalcular preço médio

1. Selecionar ativo já presente.
2. Registrar compra com preço diferente.
3. Verificar quantidade acumulada e preço médio ponderado.
4. Confirmar que o histórico mantém as duas operações.

### F-03 — Vender ativo com validação

1. Selecionar ativo com posição disponível.
2. Registrar venda parcial válida.
3. Verificar redução da quantidade e preservação do preço médio da posição
   remanescente.
4. Tentar vender quantidade superior à disponível.
5. Receber erro claro, sem alterar posição nem histórico.

### F-04 — Consultar dashboard funcional

1. Manter posições em pelo menos dois ativos.
2. Abrir o dashboard.
3. Ver custo total e gráfico de alocação por custo coerentes com as posições.
4. Registrar nova transação e verificar a atualização do resumo e do gráfico.

## 5. Dependências funcionais

| Funcionalidade | Depende de |
|---|---|
| Carteira simulada | Modelo de domínio e repositório |
| Compra simulada | Carteira, ativo, transação, validações e persistência |
| Venda simulada | Compra/posição existente, validação de disponibilidade e persistência |
| Posição atual | Histórico válido de transações e cálculo de posição |
| Preço médio | Compras ordenadas/registradas e regra decimal definida |
| Histórico | Transações e repositório SQLite |
| Dashboard CORE | Posições e agregações de custo |
| API de cotações | Contrato de provedor, cliente HTTP, configuração e fallback |
| Rentabilidade | Posição, preço médio e cotação atual |
| Alertas | API/cotações e regra configurável |
| Notificações | Alertas e provedor externo de envio |
| Planejamento/receitas/despesas/metas | Novo modelo de domínio, persistência e telas próprias |
| Valuation/preço teto | Dados fundamentalistas, premissas e métodos documentados |

## 6. POO e requisitos por módulo do CORE

| Módulo/parte | Conceitos demonstrados | Requisitos acadêmicos atendidos |
|---|---|---|
| Domínio de carteira (`Carteira`, `Ativo`, `Transação`, `Posição`) | Classes/objetos, atributos/métodos, abstração, encapsulamento, associação e composição; a carteira compõe transações/posições e protege invariantes | A-006, A-007, A-008, A-011 |
| Regras de negociação simulada | Métodos com responsabilidades claras, validação de invariantes e colaboração entre objetos | A-006, A-007, A-011; Q-001 |
| Casos de uso da aplicação | Separação de responsabilidades e coordenação sem regra na UI | A-006, A-011 |
| Repositório e SQLite | Interface/abstração de persistência e implementação substituível; polimorfismo justificável entre contrato e adaptador | A-006, A-010 quando aplicável, A-011, A-015, A-016 |
| UI PySide6 | Objetos de apresentação separados do domínio, sinais/eventos e validação de entrada | A-012, A-013, A-019, A-021 |
| Dashboard | Composição de dados e apresentação gráfica funcional | A-013, A-014 |
| Testes e documentação | Evidência das regras, modularização e capacidade de explicar decisões | A-004, A-006, A-007, A-011, A-020, A-022; Q-001/Q-003 |

Herança de classes de domínio não é obrigação do CORE. Ela só será usada se
uma relação “é um” real surgir. Não serão criadas subclasses artificiais de
compra/venda apenas para exibir herança. O polimorfismo pode ser demonstrado de
forma natural pelos contratos de infraestrutura, sem acoplar o domínio ao
banco.

## 7. Definition of Done do CORE MVP

O CORE está concluído somente quando todos os itens abaixo forem verdadeiros:

- os fluxos F-01 a F-04 passam manualmente em Windows;
- a aplicação inicia por procedimento documentado e não depende de internet;
- compras e vendas válidas persistem em SQLite após reinício;
- entradas inválidas e venda acima da posição são rejeitadas sem persistência
  parcial;
- quantidade, custo e preço médio possuem testes unitários, inclusive casos
  de borda e múltiplas compras;
- persistência possui teste de integração em banco temporário;
- UI não acessa banco nem HTTP e domínio não importa PySide6;
- dashboard usa dados reais da carteira e atualiza após transações;
- existe estado vazio e mensagens de erro claras;
- toda a suíte automatizada passa;
- instalação, execução e demonstração estão documentadas;
- arquitetura, principais classes, relações e decisões de POO podem ser
  explicadas pelo autor;
- a rastreabilidade contém evidência dos requisitos atendidos;
- não existem credenciais no código ou no repositório;
- proposta/aprovação e calendário foram confirmados com o professor.

## 8. Critério de entrada para extensões

Nenhum item de MVP EXTENDED ou OPTIONAL deve começar antes de o fluxo F-01
estar completo, persistido e testado. Itens OPTIONAL só entram após todos os
critérios da Definition of Done do CORE, exceto os artefatos finais de
apresentação.

## 9. Riscos principais e mitigação

| Risco | Mitigação |
|---|---|
| Escopo voltar a crescer para seis módulos | Usar esta classificação como gate e exigir troca explícita de escopo. |
| API indisponível comprometer a demo | Manter API fora do CORE; CORE funciona localmente com preços das transações. |
| Cálculo financeiro ambíguo | Limitar CORE a quantidade, custo e preço médio; definir precisão decimal e exemplos antes do código. |
| POO apenas formal | Modelar invariantes e colaborações reais; revisar dependências e testar domínio isoladamente. |
| Herança artificial | Tratar A-009 como condicional e justificar uso ou ausência. |
| UI concentrar regras | Casos de uso coordenam ações e domínio calcula; UI apenas coleta/exibe. |
| Falta de proposta/calendário confirmado | Resolver antes de considerar o MVP academicamente pronto. |
| Dados inválidos ou inconsistentes | Transações atômicas, validações de domínio e testes de integração. |

## 10. Fora de escopo permanente

- execução de ordens reais;
- conexão com corretoras para negociar;
- custódia de dinheiro ou ativos;
- recomendação personalizada de investimento;
- promessa de retorno financeiro.
