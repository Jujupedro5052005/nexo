# Arquitetura futura da API de mercado

## 1. Estado e limite

A API externa pertence ao MVP EXTENDED. Ela não é dependência do CORE, não é
necessária para iniciar a aplicação e não participa dos cálculos de custo e
alocação do dashboard inicial.

Nenhum provedor, endpoint ou contrato será implementado antes do gate do CORE.

## 2. Forma prevista de integração

Quando priorizada, a Application poderá definir um contrato mínimo
`MarketDataProvider` apenas com as operações exigidas pelo caso de uso, por
exemplo consultar cotação atual de um símbolo. Infrastructure conterá o
adaptador HTTP e o mapeamento da resposta externa para DTO/tipo interno.

```text
UI -> caso de uso de cotação -> MarketDataProvider <- adaptador HTTP
                                  (contrato)          (Infrastructure)
```

A UI não fará HTTP. Domain não conhecerá JSON, endpoints, chaves ou biblioteca
de rede.

## 3. Critérios antes da escolha do provedor

- documentação oficial e termos de uso;
- cobertura dos ativos necessários;
- autenticação e proteção da chave;
- limites de requisição;
- latência e disponibilidade;
- formato/precisão da cotação e horário de referência;
- permissão de cache e uso acadêmico;
- comportamento previsível para demonstração.

## 4. Resiliência futura

- timeout explícito;
- tradução de erros de rede/autenticação/limite;
- nenhuma credencial no código;
- UI responsiva durante rede;
- indicação de horário e origem da cotação;
- fallback para último valor válido somente se cache for aprovado e claramente
  identificado como desatualizado;
- testes comuns com provider falso, sem depender da internet.

## 5. Fora desta decisão

Ainda não estão definidos provedor, cache, polling, histórico de preços,
streaming ou alertas. Criar essas abstrações agora seria especulação. A
arquitetura do CORE permanece válida sem qualquer módulo de API.
