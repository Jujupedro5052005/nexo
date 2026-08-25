# Decisões do projeto

Resumo das decisões vigentes. Decisões com contexto e consequências próprias
devem receber ADR em `docs/02_architecture/decisions/`.

| Decisão | Estado/justificativa |
|---|---|
| Aplicação desktop em Python e PySide6 | Definida para a experiência e o contexto acadêmico. |
| SQLite com SQLAlchemy ou equivalente | Definido para persistência local prática. |
| Múltiplas carteiras | Cada estratégia possui identidade, histórico e resultados separados. |
| `Portfolio` persistido estruturalmente | Ao menos `id` e `name`; estado financeiro é reconstruído. |
| `Transaction` como ledger | Fonte principal de verdade financeira; ver [`ADR-001`](../02_architecture/decisions/ADR-001-transaction-ledger.md). |
| `Position` derivada | Sem tabela ou repositório próprios inicialmente. |
| `Asset` como objeto de valor | Identificado pelo símbolo; sem hierarquia por categoria. |
| Composição como relação interna principal | A carteira apresenta posições reconstruídas que contêm ativos. |
| Herança somente quando justificada | Não será usada artificialmente para demonstrar POO. |
| Polimorfismo em componentes intercambiáveis | Exemplo natural: provedores de mercado ou implementações de repositório. |
| Cálculos em `calculations` | Indicadores, projeções, risco e valuation ficam fora da UI. |
| Complementos não bloqueiam o núcleo | Planejamento, educação, IA e notificações externas têm prioridade inferior. |

Permanecem sem decisão: provedor de mercado, estratégia assíncrona da UI,
fronteira de `infrastructure/persistence`, papel de `core` e uso efetivo de
controllers/viewmodels.
