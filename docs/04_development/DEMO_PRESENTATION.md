# Apresentação ao professor

Abra `launcher.py` (código) ou `Nexo.exe` (ZIP extraído) e escolha **Apresentação**. O primeiro acesso prepara os exemplos; reabrir preserva alterações. Para começar do zero, o script `scripts/create_demo_dataset.py` recria exclusivamente o banco de apresentação, com o aplicativo fechado. Esse script exige o pacote instalado com `pip install -e .`.

## Roteiro curto

1. Selecione Longo Prazo, Dividendos ou Crescimento. Observe caixa, patrimônio, posições, resultados e concentração na Visão Geral.
2. Em Movimentações, consulte compras/vendas e eventos: abertura, aporte, retirada, dividendos, JCP com retenção, taxa e imposto. Registre um aporte e reabra o aplicativo para conferir a persistência.
3. Em Planejamento, edite orçamento e simule aportes/alocação. Em Metas, examine os três objetivos com progressos diferentes. Em Alertas, verifique as três regras locais manualmente.
4. Em Ativos e Análises, experimente PETR4, VALE3 e WEGE3 para explorar cotações, histórico, fundamentos e cenários diferentes. BOVA11 e IVVB11 exemplificam ETFs: fundamentos corporativos não se aplicam.
5. No NEXO Intelligence, pergunte sobre PETR4 ou solicite explicitamente toda a carteira. Gemini depende de chave, internet e autorização; sem chave, o provedor local é identificado. Consulte o relatório e as fontes.
6. Exporte relatórios CSV e explore a conferência parcial de IR.

## Dados e limites

Três carteiras, 93 compras/vendas, 21 posições e 16 símbolos. Operações de abril/2024 a setembro/2026; sete eventos financeiros adicionais por carteira. Orçamento de exemplo com renda de R$ 8.500 e despesas de R$ 5.200, três metas e três alertas editáveis.

Preços, históricos, fundamentos e proventos externos usam **provedores online reais**, como no ambiente pessoal. Não há atualização fictícia nem fallback para preços de exemplo. Sem conexão, cobertura ou acesso ao provedor, os indicadores correspondentes ficam indisponíveis. Somente as operações e eventos financeiros do banco de apresentação são exemplos fictícios.

Meu ambiente usa banco separado e provedores reais. Não recebe dados de apresentação como fallback. Arquivos SQLite são locais: no código, em `data/`; no executável, em `%LOCALAPPDATA%\NexoInvest`. O histórico da IA fica em outro banco. As pendências reais estão em [TODO.md](../../TODO.md).
