# Escopo do Nexo Invest

## Objetivo da primeira versão funcional

Entregar uma aplicação desktop Windows demonstrável para consultar mercado e
manter múltiplas carteiras exclusivamente simuladas. O usuário registra compras
e vendas, consulta posições reconstruídas, acompanha dashboards e compara
resultados. A entrega deve evidenciar POO real, interface útil, persistência e
ao menos uma integração válida conforme os requisitos acadêmicos.

## MUST — núcleo principal

- cadastrar, renomear, selecionar e remover carteiras simuladas conforme regras
  de segurança definidas na implementação;
- persistir ao menos `id` e `name` de cada `Portfolio`;
- registrar `Transaction` de compra e venda por carteira;
- reconstruir `Position`, quantidade, preço médio e valor investido do ledger;
- validar venda contra a quantidade disponível na carteira selecionada;
- consultar histórico separado por carteira;
- persistir dados em SQLite por repositórios da Infrastructure;
- consultar ativos/dados de mercado por um contrato da Application e adaptador
  da Infrastructure quando a integração for incluída na entrega;
- apresentar dashboard e gráfico funcional alimentados pelos dados do usuário;
- comparar pelo menos métricas definidas de duas ou mais carteiras;
- manter UI separada das regras financeiras, do SQL e do HTTP;
- funcionar somente como simulação, sem ordens reais.

## SHOULD — análise e acabamento

- exibir valor atual, lucro/prejuízo e rentabilidade quando houver cotação;
- disponibilizar indicadores e análises priorizados;
- informar origem e horário dos dados externos;
- oferecer estados vazios, validações e mensagens claras;
- permitir alertas de preço dentro da aplicação;
- manter testes unitários do domínio/cálculos e testes de integração do banco e
  do provedor de mercado.

## COULD — complementar

- projeções, risco, valuation e preço-teto;
- planejamento financeiro pessoal;
- conteúdo de educação financeira;
- notificações por e-mail ou serviços de mensagens;
- recursos de inteligência artificial;
- integrações adicionais.

Itens COULD não bloqueiam a primeira versão e só entram após estabilidade do
núcleo e revisão de prazo.

## Fora de escopo

- execução de ordens e integração com corretoras para negociar;
- custódia de dinheiro ou ativos;
- autenticação multiusuário na primeira versão;
- recomendação personalizada ou promessa de retorno;
- arquitetura distribuída, tempo real ou automação de negociação.

## Fluxos essenciais de aceite

1. Criar duas carteiras com identidades persistidas e reencontrá-las após
   reiniciar a aplicação.
2. Registrar compras em uma carteira e reconstruir quantidade e preço médio.
3. Registrar venda válida e rejeitar venda superior ao saldo sem gravação
   parcial.
4. Manter históricos e posições independentes entre carteiras.
5. Exibir dashboard baseado no estado reconstruído.
6. Comparar carteiras por métricas documentadas.
7. Consultar mercado sem UI chamar HTTP diretamente e tratar indisponibilidade.

## Definition of Done do núcleo

- fluxos essenciais passam no Windows;
- dados estruturais de carteiras e transações sobrevivem ao reinício;
- posições não são persistidas como fonte paralela;
- dinheiro usa `Decimal` nas regras;
- testes automatizados relevantes passam;
- banco e API não vazam para a UI ou Domain;
- dashboard e gráficos usam dados funcionais, não decorativos;
- instalação, execução e limitações estão documentadas quando a aplicação puder
  realmente ser executada;
- nenhum segredo está versionado;
- rastreabilidade acadêmica aponta evidências reais.

## Controle de escopo

Funcionalidades complementares não devem antecipar os modelos do domínio,
persistência de carteiras/transações, reconstrução de posições, casos de uso e
fluxos principais de UI. Mudanças de escopo exigem atualização coordenada de
requisitos, roadmap, backlog e status.
