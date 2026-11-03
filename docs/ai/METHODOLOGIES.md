# Metodologias e premissas

Cada registro possui ID, versão, descrição, classes aplicáveis, entradas,
referência de fórmula, premissas, restrições, saídas, fontes, origem, confiança,
estado de revisão e criação. Estados: `draft`, `pending_review`, `approved`,
`rejected`, `superseded`. Aprovar exige identificação do revisor e substitui a
versão anteriormente aprovada. Importação JSON nunca aprova a si própria;
IDs dos três cálculos nativos são reservados. Revisão aprova conhecimento para
contexto: não registra novas funções Python nem aceita fórmulas arbitrárias.

| ID nativo | Cálculo | Validações |
|---|---|---|
| `gordon` | D1 / (Ke − g) | D1 explícito do próximo período, origem e sustentabilidade; Ke > g; taxas em fração. |
| `target_yield` | dividendo esperado / yield alvo | Reutiliza Bazin existente; origem e sustentabilidade explícitas; yield positivo. |
| `multiples` | métrica por ação × múltiplo | LPA/P-L ou VPA/P-VP, positivos e comparabilidade justificada. FII usa somente VPA; LPA não é FFO. |

Esses modelos são implementações educacionais do Nexo, com testes conhecidos.
Não foram extraídos nem atribuídos ao Geração Dividendos. Cripto, ETF e títulos
não são compatíveis com esses três cálculos. Classes são selecionadas pelo
usuário; não há classificador automático confiável de classes/setores nesta versão.
Múltiplos não estimam enterprise value nem escolhem pares automaticamente.

Preço teto = valor teórico × (1 − desconto explícito). Default do desconto: 20%,
identificado como premissa, não como regra universal. Diferença percentual =
(valor teórico / cotação − 1) × 100; margem observada = (valor − cotação) / valor.
Não confundir desconto aplicado com margem observada. Cotação estrangeira não
é comparada a valuation BRL. Sem cotação, esses percentuais ficam ausentes.

A interface oferece campos por metodologia: valores em BRL, taxas em percentual
(digite 6 para 6%) e notas de origem/sustentabilidade/comparabilidade. Aceita
vírgula ou ponto decimal segundo a mesma gramática das telas existentes.
As taxas são normalizadas na fronteira de apresentação. O cenário JSON avançado
é opcional, para reutilizar premissas exportadas; nele as taxas usam frações.

Exemplo **sintético**, para colar no cenário JSON avançado de Gordon:

```json
{
  "expected_dividend": "3",
  "dividend_source": "premissa manual sintética de D1 por ação",
  "sustainability_note": "hipótese educacional, não previsão",
  "required_return": "0.10",
  "growth": "0.04",
  "safety_discount": "0.20"
}
```

Valor teórico 50 BRL e preço teto 40 BRL. Para yield alvo, troque Ke/g por
`"target_yield":"0.06"`. Para múltiplos, informe `metric`, `metric_per_share`,
`reference_multiple` e `comparability_note`; exemplo: eps, 4, 10, pares sintéticos.
Valores monetários decimais usam `Decimal`; evite ponto flutuante nas premissas.
Entradas têm limites de magnitude e até 12 casas decimais, evitando contextos
numéricos de tamanho arbitrário em expoentes extremos.

Ausência de dividendo é `None`; zero somente quando informado explicitamente.
Proventos históricos não são convertidos automaticamente em dividendos futuros.
Cenários variam uma premissa em ±5% e ±10%, com demais constantes; o gráfico e a
tabela mostram sensibilidade, não distribuição probabilística ou garantia.
Conservador/base/otimista resumem os preços teto desses choques sintéticos.

Extrações preservam origem `inference` até revisão; não constituem comprovação
de que um método foi ensinado na fonte. Metadados/fontes/timestamps e confiança
podem ser inspecionados na biblioteca antes de aprovar.
