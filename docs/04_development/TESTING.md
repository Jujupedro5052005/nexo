# Estratégia de testes

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
