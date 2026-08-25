# Arquitetura de serviços externos de mercado

## Estado

A consulta de mercado faz parte do produto previsto, mas ainda não está
implementada e o provedor concreto permanece indefinido. O núcleo de carteiras
deve continuar utilizável sem executar operações financeiras reais.

## Fluxo e fronteiras

```text
UI
 ↓
caso de uso em Application
 ↓
MarketDataProvider
 ↑
adaptador em infrastructure/market_data/adapters
 ↓
API financeira
```

A Application depende de um contrato mínimo orientado aos casos de uso, com
operações conceituais como `get_quote(symbol)` e `get_history(symbol)`. A
Infrastructure implementa HTTP, autenticação e conversão da resposta. A UI não
faz chamadas HTTP e o Domain não conhece JSON, endpoints ou chaves.

O polimorfismo pode surgir naturalmente se mais de um adaptador real for
necessário, mas não se criam múltiplas implementações apenas para demonstrá-lo.

## Escolha do provedor

Antes da implementação, verificar documentação oficial, cobertura de ativos,
autenticação, limites, latência, disponibilidade, precisão, horários, termos de
uso acadêmico e permissão de cache. Nenhum provedor está definido neste
documento.

## Falhas e segurança

- timeout explícito e cancelamento adequado;
- tradução de falhas de rede, autenticação e limite na Infrastructure ou
  Application;
- nenhuma chave no código ou em mensagens de erro;
- chamadas não bloqueiam a interface;
- cotações exibem origem e horário quando disponíveis;
- testes comuns usam implementação falsa; testes reais ficam na suíte de
  integração e não devem tornar a suíte dependente da internet.

Cache, polling, streaming e fallback ainda não estão definidos. Essas decisões
só devem ser tomadas quando um caso de uso concreto exigir.
