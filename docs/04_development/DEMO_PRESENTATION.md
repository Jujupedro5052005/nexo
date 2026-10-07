# Ambiente de demonstração acadêmica

**DEMO DATA — valores fictícios para apresentação.** Ativos reais da B3;
quantidades, operações, taxas, datas e preços de entrada são fictícios.
Preços foram escolhidos manualmente em faixas ilustrativas: não representam
fechamentos históricos verificados. O seed não consulta histórico nem APIs.

## Gerar e abrir

Na raiz do projeto, com o ambiente virtual ativado e o projeto instalado:

```powershell
python scripts/create_demo_dataset.py
python -m nexo.main --demo
```

Sem ativar o ambiente virtual, no Windows:

```powershell
.venv\Scripts\python.exe scripts/create_demo_dataset.py
.venv\Scripts\python.exe -m nexo.main --demo
```

O script recria **somente `data/nexo_demo.db`**. Feche o aplicativo demo antes
de recriar o arquivo no Windows. A primeira abertura com `--demo` cria o dataset
se o banco ainda não existir; outras aberturas preservam as operações registradas
durante a apresentação. O modo normal continua usando `data/nexo.db`.

O seed usa `CreatePortfolio`, `RegisterTransaction`, repositories existentes
e `LoadPortfolioPositions`. Não executa SQL de inserção diretamente, não cria
tabelas novas e não muda cálculos. Constrói e valida um arquivo temporário antes
da substituição atômica do banco demo. Recusa outro nome de arquivo e vínculos
ao banco normal. Não altera `.env`, caches ou contadores de API.

## Dataset fixo e reproduzível

Abril/2024 a setembro/2026: 30 meses, quatro compras por ativo e três vendas
parciais por carteira, com taxas entre R$ 1,90 e R$ 2,60. Compras recorrentes
representam aquisições; não são lançamentos de aporte/caixa, inexistentes no modelo.
Não simula splits, impostos, pagamentos de proventos ou conversões de ticker.

| Carteira | Perfil | Ativos | Movimentações | Custo aberto | Valor aberto observado* |
|---|---|---:|---:|---:|---:|
| Longo Prazo | Diversificada, ações e ETFs | 8 | 35 | R$ 104.014,40 | R$ 138.442,80 |
| Dividendos | Empresas para consultar proventos | 7 | 31 | R$ 59.923,28 | R$ 74.507,84 |
| Crescimento | Menor, pesos e resultado distintos | 6 | 27 | R$ 40.561,16 | R$ 49.149,36 |

*Fotografia dos providers durante a validação em 07/10/2026; não é valor fixo do
seed ou patrimônio incluindo caixa. Novas aberturas consultarão preços disponíveis
naquele momento, respeitando a configuração, plano e budgets. Lucro/prejuízo
por posição pode mudar. Na fotografia conferida, todas as carteiras tinham
posições ganhadoras e perdedoras. Total: **93 movimentações e 21 posições**,
representando **16 tickers distintos**.

- Longo Prazo: ITUB4, PETR4, VALE3, WEGE3, BBAS3, B3SA3, IVVB11, BOVA11.
- Dividendos: BBAS3, TAEE11, ITSA4, PETR4, BBSE3, EGIE3, B3SA3.
- Crescimento: WEGE3, RENT3, TOTS3, RADL3, PRIO3, IVVB11.

## Telas e gráficos conferidos

Aplicativo aberto com o banco demo na interface nativa Windows; dez páginas
navegadas. Resultados locais e gráficos também verificados automaticamente,
com providers de teste somente nos testes. Capturas e relatório sanitizado em
`tmp/demo_presentation/` ficam fora do versionamento.

| Tela/gráfico | Dados necessários | Dataset preenche? | Resultado |
|---|---|---|---|
| Dashboard: custo, realizado e contagens | Histórico local | Sim | Preenchido ao abrir Longo Prazo |
| Valor, não realizado e retorno aberto | Posições + cotações BRL completas | Histórico sim; preços externos | Completo nas três carteiras na validação |
| Posições | Reconstrução do histórico | Sim | 8 / 7 / 6 posições |
| Barras de custo versus valor | Posições + cotações | Histórico sim; preços externos | Gráfico nas três carteiras |
| Concentração/alocação por ativo | Valuation BRL completo | Histórico sim; preços externos | Pesos, maior/top 3/HHI, donut e tabela completa |
| Comparação | Duas ou mais carteiras + valuation | Sim, condicionado às cotações | Três carteiras, 21 linhas e gráfico |
| Movimentações e filtros | Histórico por carteira | Sim | 35 / 31 / 27 linhas; compras e vendas |
| Gráfico temporal de movimentações | Funcionalidade própria | Não se aplica | Não há gráfico; existe tabela filtrável |
| Ativos: snapshot e linha histórica | Quote + histórico externo | Tickers sim; dados externos | PETR4 e B3SA3 com OHLCV e 21 pontos de 1 mês |
| Análise: proventos e Bazin | Distribuições externas + yield explícito | Tickers sim; dados externos | Quatro eventos em cada ativo; consultar com yield 6% |
| Análise: barras de preços/modelos | Quote e modelos calculáveis | Parcial | Cotação/Bazin disponíveis; Graham depende de fundamentos |
| Fundamentos, Graham, cadastro e DFP/ITR | bolsai e identidade para CVM | Não depende do ledger | Indisponíveis na sessão sem chave bolsai |
| Evolução patrimonial e referência | Série própria da carteira | Não | Gráfico demonstrativo já existente; seed não o alimenta |
| Alocação por categoria | Categorias/modelo correspondente | Não se aplica | Não há gráfico funcional por categoria |
| Planejamento, metas, alertas e relatórios | Backends dessas funcionalidades | Não | Telas demonstrativas; não derivadas do banco demo |
| Configurações/saúde de providers | Configuração e contadores locais | Não depende do seed | Diagnóstico disponível |

Proventos são apresentados como resumo/eventos externos, não como um novo gráfico
ou saldo da carteira. Yahoo mantém `CASH_DISTRIBUTION`, não diferencia JCP/dividendo
e usa data-ex quando pagamento é desconhecido. Bazin conserva essas limitações.

## Providers e economia

Seed e testes: **zero operações externas**. A primeira avaliação das carteiras
deduplica os 16 símbolos; a navegação reaproveita o cache compartilhado. Não há
uma consulta por movimentação ou polling. Cache de mercado em memória não
sobrevive ao encerramento da aplicação; contadores de consumo sobrevivem.

Na conferência online e sua complementação: brapi **20**, Yahoo **2**, bolsai
**0**, CVM **0** operações. A complementação visual reutilizou respostas reais
capturadas, preservando valores, fonte e horários, para evitar consultar novamente
os 16 ativos. Nenhum preço fictício foi injetado no modo demo do produto.

Os cinco tickers prioritários PETR4, ITSA4, B3SA3, VALE3 e WEGE3 tiveram cotação.
**PETR4 e B3SA3** tiveram também análise conferida: preço, variação, OHLCV,
histórico, distribuições e fonte. Ambos são boas escolhas para a gravação na
configuração atual, mas fundamentos/cadastro não estarão completos sem bolsai.
Na consulta separada do snapshot B3SA3 houve uma falha transitória; a análise
subsequente recebeu cotação válida. Prefira PETR4 na abertura da demonstração
e confira o snapshot de B3SA3 antes de gravar. Não há garantia de disponibilidade
externa em toda chamada, mesmo quando a configuração permite o ativo.
O seed não deve habilitar fallbacks pagos, ignorar budgets ou alterar credenciais.

Verificação manual reproduzível, opcional e com acesso real à rede:

```powershell
python scripts/check_demo_presentation.py --online
```

Esse comando abre e encerra o aplicativo, navega pelas páginas, compara carteiras,
consulta PETR4/B3SA3 e salva capturas/JSON em `tmp/demo_presentation/`. Não reseta
o seed. Pode consumir aproximadamente 16 consultas de cotação e as consultas
de histórico/proventos dos dois ativos; configuração e fallbacks afetam o total.
Não rode repetidamente: respeite o budget e aproveite a sessão aberta.

## Roteiro de 90 segundos

1. **0–15 s:** abrir `--demo`; mostrar as três carteiras e os KPIs de Longo Prazo,
   explicando que são operações fictícias com preços de mercado consultados.
2. **15–30 s:** mostrar posições, BBAS3 em prejuízo na fotografia e barras de
   custo/valor e concentração; trocar para Dividendos ou Crescimento.
3. **30–45 s:** em Movimentações, mostrar compras recorrentes e filtrar SELL.
   Se desejar, registrar compra de 1 PETR4 com preço exibido e taxa zero;
   o histórico e as posições atualizam e a operação permanece no banco demo.
4. **45–60 s:** Análises → Carteiras / comparação; selecionar as três carteiras
   e comparar custos, valores, resultados e pesos.
5. **60–80 s:** Ativos → buscar PETR4, selecionar e mostrar snapshot, linha
   histórica e fonte; usar yield requerido de 6% para demonstrar Bazin.
6. **80–90 s:** mostrar B3SA3 ou o resumo de proventos; explicar a limitação
   dos fundamentos e encerrar na comparação.

Prepare as consultas na mesma sessão antes de gravar; evite atualizar mercado
repetidamente. Após gravar, feche o app e execute o seed para restaurar o cenário.

## Limites preservados

Valor aberto não é patrimônio total com caixa; retorno aberto não é rentabilidade
histórica/TWR. XIRR, Sharpe, benchmark funcional, caixa e aportes/retiradas
explícitos não estão implementados. Nenhum histórico de compras, por mais longo
que seja, supre automaticamente essas informações. Falhas/quotas dos providers
mantêm as métricas externas indisponíveis; o modo demo não mascara isso.
