# Metodologias e premissas

Cada registro possui ID, versão, descrição, classes aplicáveis, entradas,
referência de fórmula, premissas, restrições, saídas, fontes, origem, confiança,
estado de revisão e criação. Estados: `draft`, `pending_review`, `approved`,
`rejected`, `superseded`. Aprovar exige identificação do revisor e substitui a
versão anteriormente aprovada. Importação JSON nunca aprova a si própria;
IDs dos quatro cálculos nativos são reservados. Revisão aprova conhecimento para
contexto: não registra novas funções Python nem aceita fórmulas arbitrárias.

| ID nativo | Cálculo | Validações |
|---|---|---|
| `gordon` | D1 / (Ke − g) | D1 explícito do próximo período, origem e sustentabilidade; Ke > g; taxas em fração. |
| `target_yield` | dividendo esperado / yield alvo | Reutiliza Bazin existente; origem e sustentabilidade explícitas; yield positivo. |
| `bank_residual` | VPA × (ROE − g) / (Ke − g) | Banco identificado, VPA positivo, ROE ≥ g, Ke > g. Retorno excedente estável. |
| `multiples` | métrica por ação × múltiplo | LPA/P-L ou VPA/P-VP, positivos e comparabilidade justificada. FII usa somente VPA; LPA não é FFO. |

Esses modelos são implementações educacionais do Nexo, com testes conhecidos.
Não foram extraídos nem atribuídos ao Geração Dividendos. Cripto, ETF e títulos
não recebem cenários automáticos. O modo manual usa a classe selecionada.
A investigação reconhece um cadastro restrito de emissores, identificado no
relatório. Final 11 não implica FII. Outros ficam sem classificação.
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
No modo manual, proventos históricos não substituem D1 explícito.
Cenários variam uma premissa em ±5% e ±10%, com demais constantes; o gráfico e a
tabela mostram sensibilidade, não distribuição probabilística ou garantia.
Conservador/base/otimista resumem os preços teto desses choques sintéticos.

Extrações preservam origem `inference` até revisão; não constituem comprovação
de que um método foi ensinado na fonte. Metadados/fontes/timestamps e confiança
podem ser inspecionados na biblioteca antes de aprovar.

## Cenários assistidos e pareceres

Permitir estimativas no modo aprofundado autoriza três hipóteses identificadas.
Defaults ilustrativos Nexo v2:

| Cenário | Ke | g | Yield alvo |
|---|---:|---:|---:|
| Conservador | 16% | 2% | 10% |
| Base | 14% | 3% | 8% |
| Otimista | 12% | 4% | 6% |

Gemini pode propor valores dentro do schema: Ke 6–40%, g −5–6%, yield 3–20%,
justificativa obrigatória, Ke > g. Não são taxas atuais observadas. Desativar
estimativas conserva dados e remove valuations assistidos. Premissas do usuário
prevalecem. Pedir margem de 25% altera o desconto e recalcula localmente.

Bancos reconhecidos usam VPA/ROE observados e retorno excedente estável. Outros
ativos reconhecidos usam distribuições históricas elegíveis, supondo repetição
como hipótese futura explícita. JCP identificado é excluído; distribuição
`CASH_DISTRIBUTION` genérica é marcada como bruta sem separação tributária.
Ausência não vira zero. LPA × 10 serve apenas como verificação ilustrativa;
10 não é múltiplo observado de pares.

Preço abaixo do teto base permite parecer favorável sob essas hipóteses.
Concentração acima de 25% gera ressalva de ampliação: limiar de política
ilustrativa Nexo. Dados sem data/antigos pedem confirmação. Não há previsão de
preço ou probabilidades. Cada ativo inclui critérios de revisão, proveniência,
fórmulas, entradas, fontes e datas. Correlação exige intervalos coincidentes,
séries ajustadas e ao menos 20 pares de retornos. Não preenche buracos.
