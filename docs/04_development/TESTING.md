# Estratégia de testes

## Suíte implementada — incremento 01

43 casos: 11 de Domain, 6 de Application, 7 de SQLite e 19 de UI,
incluindo os 9 smoke tests anteriores. Unitários e a maioria dos testes de UI
usam um repository em memória definido somente em `tests/conftest.py`.

Integração cobre schema exclusivo de portfolios, IDs, nomes duplicados,
reabertura com novo engine/repository e rollback após flush. Um fluxo de UI
cria em SQLite temporário e verifica outra janela após reabertura.
Não há teste financeiro nem dependência de API/rede; `data/nexo.db` não é usado.
O restante deste documento descreve a estratégia para incrementos futuros.

```text
tests/
├── unit/
│   ├── domain/
│   ├── application/
│   └── calculations/
├── integration/
│   ├── database/
│   ├── market_data/
│   └── notifications/
├── ui/
└── fixtures/
```

## Unitários

Domain e Calculations devem ter cobertura forte de invariantes, `Decimal`,
compras, vendas, preço médio, reconstrução de posições, isolamento entre
carteiras e métricas. Application é testada com repositórios e providers falsos
para verificar coordenação e falhas sem banco ou rede.

## Integração

Banco: schema, mapeamento ORM/domínio, vínculo por `portfolio_id`, rollback,
persistência após reabertura e preservação de datas/decimais.

Dados de mercado e notificações: contratos, conversão de respostas, timeouts e
erros. Testes reais de serviços externos devem ser separados da suíte comum e
nunca exigir credenciais versionadas.

## UI

Quando viável, usar pytest-qt para seleção de carteira, submissão de formulários,
mensagens, estados vazios e atualização de telas com casos de uso falsos. Manter
também roteiro manual dos fluxos críticos no Windows.

## Execução

```powershell
pytest
pytest --cov=src/nexo
```

Estrutura vazia ou teste planejado não conta como evidência de requisito
atendido. A suíte deve permanecer determinística e independente da internet por
padrão.
