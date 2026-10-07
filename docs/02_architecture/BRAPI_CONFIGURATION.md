# Configuração e diagnóstico brapi — Incremento 05.1

## Auditoria e causa observada

Antes do 05.1, MarketSettings.from_environment já chamava python-dotenv.load_dotenv
com .env da raiz do checkout e override=False. main.py já passava esse resultado
a BrapiMarketDataProvider. python-dotenv já constava de requirements.txt; pyproject
deriva dependências desse arquivo. Não foi adicionada dependência.

ITSA3 sem chave era corretamente barrado antes do HTTP, mas a mensagem era curta
e Configurações ainda mostrava provider não configurado de forma demonstrativa.
MARKET_API_KEY/MARKET_API_BASE_URL são campos legados não lidos pelo adapter brapi;
um .env contendo somente esses nomes não configura BRAPI_TOKEN.

## Arquivo e precedência

Arquivo local: .env na raiz do checkout, carregado automaticamente ao iniciar ou
reiniciar o Nexo. Leitura UTF-8 com ou sem BOM; não depende de cwd. Parâmetro
opcional env_path permite testes isolados, sem ler o arquivo ou chave do usuário.

1. Para cada nome, ambiente exportado ganha do mesmo nome no arquivo.
2. Após carregar, BRAPI_TOKEN não vazio ganha de BRAPI_API_KEY não vazio.
3. Ambos vazios/ausentes: sandbox público. Whitespace isolado é vazio.

A ordem de nomes vale depois da ordem por origem: TOKEN no arquivo pode ganhar de
API_KEY no ambiente. Variável vazia já exportada não é preenchida pelo arquivo;
remova a variável se quiser reutilizar o valor do arquivo. BRAPI_BATCH_SIZE mantém
padrão 1 (free) e clamp 1–100. Acima de 1 exige plano compatível. A política
multi-provider atual está em [DATA_PROVIDERS.md](DATA_PROVIDERS.md).

.env.example contém BRAPI_TOKEN vazio, dashboard, alias comentado e batch; os
campos MARKET_API_* foram removidos do template para evitar ambiguidade. Arquivo
.env do usuário não é alterado pela UI ou pelo incremento.

## Contrato e camada de aplicação

MarketIntegrationStatus é DTO imutável sem token: provider, configured,
authenticated (bool/None), public_symbols, message e state. MarketDataProvider tem
capability opcional get_integration_status; implementações antigas continuam
válidas. CachedMarketDataProvider delega essa capability sem HTTP ou cache secreto.

GetMarketIntegrationStatus recebe apenas o contrato. TestMarketConnection recebe
o mesmo adapter não cacheado de main.py e faz uma quote de PETR4; não cria client,
não reutiliza cache como se fosse teste de rede e não altera cálculos/ledger.

Configured informa presença de chave. Authenticated=None significa não verificada.
Como PETR4 é público, 200 no teste comprova conexão/consulta, não acesso autenticado
a ativos protegidos. Em modo autenticado, o Bearer é enviado, mas a UI explica esse
limite. O teste não faz segunda chamada a um ativo protegido sem necessidade.

## Capabilities e erros

Lista de ações públicas centralizada em infrastructure/market_data/config.py:
PETR4, MGLU3, VALE3 e ITUB4. Adapter e DTO compartilham essa lista; UI não a duplica.
[Autenticação oficial](https://web-next.brapi.dev/docs/authentication) e
[cotação v2](https://web-next.brapi.dev/docs/acoes/cotacao), consultadas em 06/10/2026.

| Situação | Classificação | Diagnóstico |
|---|---|---|
| ITSA3 sem chave | MarketCredentialsRequiredError | Existe na busca; detalhes exigem configuração, sem HTTP |
| 401 | MarketInvalidTokenError | Chave recusada; authenticated=False |
| 403 | MarketPlanAccessError | Recurso fora do plano; authenticated=True quando chave configurada, conforme contrato oficial |
| 429 | MarketRateLimitError | Limite atingido; authenticated=None |
| Timeout/conexão | MarketDataUnavailableError | Verificar conexão; authenticated=None |
| 404 | AssetNotFoundError | Mantém semântica de ativo sem dados, distinta de configuração |

As três especializações novas herdam MarketAuthenticationError para preservar
compatibilidade com os 432 testes e consumidores anteriores. Não há inspeção de
texto de erro para decidir estado. Corpos de resposta/erros de transporte não são
expostos; falhas inesperadas de worker produzem mensagem genérica na UI.

## UI e segurança

Seção funcional de mercado em Configurações: brapi, configurado/não configurado,
modo, autenticação, orientação .env/reinício e Testar conexão. Só informa “chave
configurada”, sem máscara parcial ou caracteres da chave. Demais seções de
Configurações permanecem fora do escopo desta estabilização.

Ativos distingue resultado de catálogo de permissão para detalhes. ITSA3 mostra
explicação pública/capability e ação Configurar integração → Configurações. Não
abre editor externo. Busca e ledger offline permanecem disponíveis.

Teste executa em TaskRunner, com callbacks na GUI, botão desabilitado durante voo
e geração contra resposta antiga. MainWindow/main incluem esse runner no stop/wait
antes de fechar client/engine. HTTP e credenciais seguem exclusivamente na infra.

.env/.env.* continuam ignorados, com exceção do template. Token nunca vai para URL,
repr, status, UI, logs, traceback traduzido ou SQLite. Nenhuma tabela/configuração
persistida nova; sem edição de segredo na UI ou alteração do .env existente.

## Verificação

35 novos casos em tests/brapi_config: arquivo/cwd/BOM/precedência/alias, sandbox,
ITSA3/configuração versus inexistente, Bearer fake controlado, status/segurança,
401/403/429/timeout, UI/navegação/heartbeat e falha inesperada segura.

Windows: consulta real PETR4 sem token e Testar conexão público funcionaram;
ITSA3 sem token foi classificado localmente como configuração necessária.
Nenhuma chave real estava disponível na configuração externa da sessão; ITSA3
com chave foi validado somente com MockTransport e Bearer fictício. Não se afirma
sucesso autenticado real. Testes normais não dependem de rede ou credenciais reais.

Arquitetura financeira e entregas 01–05 preservadas; caixa/fluxos/TWR/alertas/metas/
planejamento e novas tabelas não implementados. Execução normal e alternativa
PowerShell em [README](../../README.md); resultados em
[TESTING.md](../04_development/TESTING.md).
