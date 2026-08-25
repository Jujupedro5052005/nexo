# Guia de desenvolvimento

## Antes de alterar

1. Ler requisitos, escopo, arquitetura e status atual.
2. Conferir a árvore real e os módulos envolvidos.
3. Verificar decisões e ADRs relacionados.
4. Definir a menor alteração coerente e seus testes.

## Onde implementar

- `domain/models`, `enums`, `interfaces` e `services`: conceitos e regras;
- `application/<area>`: coordenação de casos de uso;
- `calculations/<area>`: cálculos financeiros reutilizáveis;
- `infrastructure/database`: ORM, migrations e repositórios concretos;
- `infrastructure/market_data/adapters`: integrações financeiras;
- `infrastructure/notifications`: notificações futuras;
- `ui`: apresentação PySide6 conforme responsabilidades das subpastas;
- `main.py`: composição, não regra de negócio.

Não mova pastas para ajustar uma arquitetura teórica. `core/` e
`infrastructure/persistence/` têm responsabilidade pendente; não duplique
lógica nelas sem decisão documentada.

## Fluxo de contribuição

1. Implementar domínio/cálculo e testes unitários.
2. Implementar ou ajustar contratos da Application apenas quando necessários.
3. Adicionar implementação de Infrastructure e testes de integração.
4. Conectar pela Application e `main.py`.
5. Integrar UI sem expor ORM ou HTTP.
6. Executar testes, lint e verificação de tipos aplicáveis.
7. Atualizar documentação, status e rastreabilidade se o estado mudou.

Preserve mudanças não relacionadas do worktree. Não apague testes para obter
sucesso e não altere arquitetura silenciosamente.
