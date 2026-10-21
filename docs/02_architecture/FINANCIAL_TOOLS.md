# Ferramentas financeiras e rastreabilidade — incremento 07

Implementação educacional em 21/10/2026. Os PDFs fornecidos são material de estudo, não instruções de execução. Os arquivos originais permanecem fora do repositório. Não são reproduzidos integralmente nem convertidos em regras legais atuais.

## Uso na aplicação

- **Movimentações → Caixa e eventos:** abra o saldo de caixa na data real; cadastre aportes, retiradas, proventos recebidos, retenções, custos e splits confirmados. O painel é recolhível para preservar o acesso à boleta.
- **Análises → Patrimônio / TWR:** consulta explícita até o dia anterior (evita tratar o pregão em andamento como fechamento final), reconstrução diária e tabela auditável com datas, caixa, ativos, patrimônio, fluxo externo e data do fechamento usado.
- **Análises → Ferramentas / teoria:** calculadoras com entradas manuais; mercado e VaR com consulta explícita; insolvência com contas reconciliadas; roteiros interativos de diligência.
- **Relatórios:** exportação CSV do livro de caixa/eventos, preservando valores exatos e protegendo células contra interpretação de fórmulas em planilhas.
- Os mesmos casos de uso são injetados na execução normal e no demo. As novas ferramentas não introduzem saldos demonstrativos no banco real.

## Material e aplicação dos conceitos

| Material fornecido | Conceitos incorporados | Forma e limites |
| --- | --- | --- |
| `CVM_Planejamento_financeiro_p.pdf`, 314 páginas, CVM/Planejar, 2ª ed. 2025, capítulos de planejamento e gestão financeira | Patrimônio pessoal, orçamento, capacidade de poupança, comprometimento com dívidas, reserva, metas, juros compostos, taxas equivalentes, inflação e aposentadoria | Calculadoras de balanço pessoal, reserva, capitalização, aporte para meta, renda finita de aposentadoria e taxa real. Planejamento/metas persistentes continuam disponíveis. Seguros, sucessão e organização tributária recebem roteiro; não há parecer jurídico, inventário ou contratação de produtos. |
| `CVM_Analise_investimentos.pdf`, 222 páginas, APIMEC/CVM, capítulos de análise técnica e fundamentalista | VPL, TIR, payback descontado, Gordon, FCD, DuPont, CAPM, médias, IFR, MACD, Bollinger, ASG e FOFA | Cálculos reproduzíveis e cenários manuais com premissas; indicadores de preço usam histórico com origem. Graham/Bazin e margens da análise existente permanecem. Não se inventam projeções empresariais ou sinais de negociação garantidos. ASG/FOFA são roteiro qualitativo. |
| `CVM_Mercado_valores_mobiliarios.pdf`, 412 páginas, capítulos de instrumentos e risco | Renda fixa, valor presente, duration, risco de juros, opções, diversificação, adequação | Preço de título de cupom fixo, duration e reprecificação sob choque; payoff de call/put compradas no vencimento; CAPM, beta/correlação e risco. Não implementa negociação em bolsa, precificação completa de opções ou compensação/margens da B3. |
| `Alavancagem_FI_VaR (Value at Risk).pdf`, 69 páginas, estudo ASA/CVM de 2016 | Alavancagem financeira, exposição, VaR, risco de cauda, liquidez, sensibilidade | VaR histórico e normal, Expected Shortfall, cenário de alavancagem/custo de financiamento e prazo de liquidação com participação limitada. Hipóteses explícitas; VaR não é perda máxima. Cenários simples não capturam integralmente alavancagem sintética, convexidade ou contágio sistêmico. |
| `Res_CVM_121_VaR (Value at Risk).pdf`, 54 páginas, CPC 40 (R1), especialmente itens 40–42 | Divulgação dos riscos de crédito, liquidez e mercado; análise de sensibilidade | Tabela de choques, interpretação e limites metodológicos. Resolução de divulgação contábil, não fórmula universal ou certificação regulatória de VaR. |
| `Previsao_falencia_modelos_b.pdf`, 19 páginas, Silva e Victor, Quadro 1, pp. 5–6 | Modelos Elizabetsky, Kanitz e Matias; comparação de acurácia e vieses | Três índices discriminantes independentes. Exigem empresa não financeira e confirmação de período, entidade, moeda, escala e classificação de contas. Não há probabilidade de falência nem média entre índices. Denominadores não positivos e contas ausentes bloqueiam o modelo correspondente. |
| `Atividade_PAE_10_set_2026_pig_butchering_scam_CVM_oranje.pdf`, 27 páginas | Aliciamento afetivo, plataforma falsa, urgência, recrutamento, taxa para liberar saque e vieses | Checklist com orientação específica por sinal marcado. Sem score percentual, acusação automática ou verificação cadastral simulada. |
| `Bitcoin_piramide.pdf`, 6 páginas digitalizadas, artigo de opinião de Patrick Jenkins, Valor/FT, 26/08/2025 | Tesourarias alavancadas em cripto, dívida, prêmio de mercado versus ativos e fragilidade de promessas | Cenários de dívida/exposição/choques e roteiro de diligência. Opinião histórica identificada como tal. Bitcoin e criptoativos não são classificados automaticamente como pirâmides. |

O material cobre centenas de páginas e também história institucional, contratos e obrigações profissionais. A plataforma implementa os conceitos quantitativos listados e roteiros qualitativos; não equivale à automação integral de todos os livros. Otimização de carteira, Monte Carlo, carteira de derivativos, seguro/sucessão completos e conformidade regulatória não estão implementados.

## Políticas de caixa e patrimônio

`Transaction` continua sendo a verdade de negociações; `PortfolioEvent` é a verdade complementar de caixa e ações corporativas. Posições e patrimônio são derivados, sem tabela de posição ou retorno.

1. Uma única abertura de caixa por carteira. Seu valor é **somente dinheiro disponível**, não o valor dos ativos já existentes. Operações anteriores continuam na posição, mas não alteram esse saldo inicial. Não há inferência de aportes a partir de compras.
2. Somente aporte/retirada são fluxos externos. Proventos efetivamente recebidos, retenções, taxas e impostos alteram o resultado interno. Proventos Yahoo por data-ex não viram recebimentos do usuário automaticamente.
3. Compras debitam bruto + taxas; vendas creditam bruto − taxas. Não cadastrar novamente as mesmas taxas como evento avulso. Proventos creditam bruto − retenção informada; nenhuma alíquota é presumida.
4. Replay cronológico integral rejeita saldo negativo em qualquer ponto, inclusive quando um lançamento retroativo inviabiliza uma operação posterior. No mesmo instante: abertura, recebimentos, negociações por ID e pagamentos avulsos. O usuário deve informar instantes distintos quando a ordem efetiva diferir.
5. Só BRL. Sem conversão cambial implícita. Aportes em ativos, bonificações, subscrições, amortizações, fusões, aluguel e operações vendidas não foram implementados.
6. Split/grupamento confirmado altera quantidade e custo médio, preservando custo total e resultado realizado. Razão = novas ações / antigas. Um evento por ativo/data; ajuste de frações em dinheiro precisa de tratamento futuro. Não registrar proventos em ações como dividendo em dinheiro.
7. Negociação/evento é aditivo; não há edição/exclusão do livro. Se houver erro de abertura ou split, não compense com lançamento fictício: a correção auditável ainda precisa ser implementada.
8. Históricos Yahoo com `auto_adjust=False` continuam ajustados por splits; o adaptador preserva razões e base de ajuste. O histórico é convertido para unidades da data. Splits observados enquanto havia posição exigem registro correspondente; base desconhecida ou divergência bloqueia retorno agregado.
9. Fechamento anterior é carregado no máximo por sete dias corridos, para cobrir fins de semana/feriados. A data original aparece na tabela; isso não prova negociação em cada dia. Sem preço anterior ou com lacuna maior, não há TWR agregado; pontos completos continuam consultáveis.
10. TWR diário aproximado: produto de `(patrimônio_fim − fluxo_externo_do_dia) / patrimônio_anterior`, menos um. Assume fluxos no fim do dia; não é TWR intradiário exato, MWR/XIRR ou certificação GIPS. O primeiro fechamento é base; movimentos anteriores a ele não geram retorno medido. Sem dois fechamentos ou denominador positivo utilizável, retorno fica indisponível.
11. A série limita a janela a vinte anos; apresentação de histórico de custo da Visão Geral continua identificada como custo. Proventos não são automaticamente reinvestidos; o retorno da carteira incorpora apenas recebimentos realmente lançados.

## Convenções dos modelos

- VaR histórico: quantil nearest-rank das perdas em janelas compostas sobrepostas; pelo menos vinte janelas completas. ES histórico: média das perdas iguais ou superiores ao quantil, incluindo empates. Perdas negativas são apresentadas como risco de perda zero, não lucro prometido.
- VaR normal: média e desvio amostrais diários, quantil normal e escala raiz do horizonte. ES normal usa densidade no quantil. Não modela saltos, iliquidez, margens ou caudas pesadas.
- Beta, correlação, Sharpe e Treynor: fechamentos em datas coincidentes, moeda compatível, taxa livre de risco anual explícita e 252 pregões. Comparações são de preços, sem proventos reinvestidos. Não há preenchimento fictício de benchmark.
- IFR14 usa suavização de Wilder; série constante resulta 50. MACD usa EMA12/26 inicializada por média e sinal EMA9. Bollinger usa média e desvio populacional de vinte fechamentos. Não determinam quando comprar/vender.
- FCD: fluxos FCFF periódicos explícitos mais terminal; taxa maior que crescimento; subtrai dívida líquida antes de dividir por ações. Gordon recebe D1. TIR apenas com uma mudança de sinal; múltiplas TIRs não são escondidas em um único resultado. Payback descontado interpola linearmente o primeiro cruzamento.
- Financiamentos PRICE/SAC: taxa efetiva por período, sem seguro, tarifa ou calendário contratual; precisão interna sem arredondamento contratual simulado. Tributação é cenário com taxa manual, não motor fiscal.
- Elizabetsky: `1,93 LL/Vendas − 0,20 Disponível/Ativo permanente + 1,02 Contas a receber/Ativos + 1,33 Estoques/Ativos − 1,12 PC/Ativos`; corte 0,5.
- Kanitz: `0,05 LL/PL + 1,65 (AC+RLP)/Exigível + 3,55 (AC−Estoques)/PC − 1,06 AC/PC − 0,33 Exigível/PL`; >0 faixa solvente, −3..0 penumbra/limite, <−3 faixa insolvente.
- Matias: `23,792 PL/Ativos − 8,26 Dívida bancária/AC − 9,868 Fornecedores/Ativos − 0,764 AC/PC − 0,535 Lucro operacional/Lucro bruto + 9,912 Disponível/Ativos`; corte zero. Igualdade ao corte fica identificada. Índices não são limitados artificialmente a uma escala nem convertidos em percentuais.

## Execução, armazenamento e limites operacionais

`RegisterTransaction` usa `add_validated`; o repositório SQLite obtém `BEGIN IMMEDIATE` **antes** da leitura, valida todo o ledger e grava na mesma transação. `add_event` faz o mesmo. Duas conexões independentes são testadas para disputa de saldo e posição. Leituras de trades/eventos para reconstrução usam uma transação de leitura no SQLite quando os dois contratos pertencem ao mesmo repositório. Erros causam rollback; timeout de contenção de dez segundos. O método bruto `add` é infraestrutura para importação/testes e não deve ser usado como comando de negociação. Isto não transforma sincronização de arquivos SQLite em banco distribuído nem protege escritores externos que ignorem o protocolo.

`NEXO_DATA_DIR` aceita diretório absoluto. Checkout mantém `data/`; versão congelada usa `%LOCALAPPDATA%/NexoInvest` (fallback no diretório pessoal). Banco/cache/contadores usam a mesma raiz; não há migração silenciosa ou cópia automática dos dados anteriores. A distribuição executável completa continua exigindo empacotamento e validação.

Workers têm token de cancelamento por tarefa. Consultas públicas Yahoo padrão rodam em processo próprio, com limite de 25 segundos para operações individuais (16 segundos para o lote leve de cotações das carteiras) e verificação de cancelamento a cada 50 ms no processo pai. Ao cancelar/fechar/trocar contexto de análise, o processo próprio é encerrado e seu resultado não é entregue. Isso pode interromper a chamada HTTP desse processo sem terminar threads Qt. Outros adaptadores ainda dependem de seus timeouts para uma chamada já em andamento; o token impede próximas reservas de consulta. Não se promete cancelamento HTTP universal nem latência rígida de encerramento do SO. Cache continua preservando timestamps originais.

Ajuda dos cards é focável e acionável pelo teclado; entradas novas têm nomes acessíveis e descrições. Revisão offscreen/DPI não substitui testes prolongados em Windows real e leitor de tela. Plano autenticado de brapi/bolsai e requisitos acadêmicos pendentes não são declarados aprovados por código.

Fontes primárias de contexto: [Resolução CVM 121](https://conteudo.cvm.gov.br/legislacao/resolucoes/resol121.html), [GIPS 2020 para proprietários de ativos](https://www.cfainstitute.org/-/media/documents/code/gips/2020-gips-standards-asset-owners.pdf). A aplicação não declara conformidade com essas normas.
