"""User-controlled financial scenarios. Inputs never impersonate market/account data."""

from dataclasses import dataclass
from decimal import Decimal, localcontext

from nexo.calculations.precision import financial_context
from nexo.calculations.projections.finance import (
    amortization,
    bond_metrics,
    discounted_company,
    future_value,
    irr,
    npv,
    real_rate,
    required_payment,
    valid_rate,
)
from nexo.domain.errors import DomainValidationError


@dataclass(frozen=True)
class ToolField:
    key: str
    label: str
    help: str
    kind: str = "number"
    default: str = ""


@dataclass(frozen=True)
class ResearchResult:
    rows: tuple[tuple[str, Decimal | None, str, str], ...]
    explanation: str


@dataclass(frozen=True)
class ToolSpec:
    key: str
    title: str
    description: str
    fields: tuple[ToolField, ...]
    reference: str


def field(
    key: str, label: str, help: str, kind: str = "number", default: str = ""
) -> ToolField:
    return ToolField(key, label, help, kind, default)


CAPITAL = field(
    "capital",
    "Capital inicial (R$)",
    "Valor informado manualmente. Não é o saldo da carteira.",
)
RATE = field(
    "rate",
    "Taxa por período (%)",
    "Hipótese nominal efetiva por período; pode ser negativa, acima de −100%.",
    "percent",
)
PERIODS = field(
    "periods",
    "Número de períodos",
    "Inteiro; a taxa e os pagamentos devem usar a mesma unidade de tempo.",
    "int",
)
PAYMENT = field(
    "payment",
    "Aporte no fim do período (R$)",
    "Aportes constantes no fim de cada período; não são registrados no ledger.",
)
FLOWS = field(
    "flows",
    "Fluxos periódicos, separados por ;",
    "Inclua t=0. Exemplo: -1000; 400; 400; 400. Todos os fluxos na mesma moeda.",
    "series",
)
DISCOUNT = field(
    "discount",
    "Taxa de desconto por período (%)",
    "Custo de oportunidade informado pelo usuário. Não é previsão de retorno.",
    "percent",
)
GROWTH = field(
    "growth",
    "Crescimento perpétuo (%)",
    "Hipótese de longo prazo, menor que a taxa de desconto.",
    "percent",
)
PLAN = "CVM/Planejar, Planejamento Financeiro Pessoal, caps.1–4 (PDF fornecido, edição 2025)."
ANALYSIS = (
    "CVM/APIMEC, Análise de Investimentos, cap.4 (FCD, Gordon, múltiplos e DuPont)."
)
MARKET = (
    "CVM, Mercado de Valores Mobiliários; conceitos de renda fixa, derivativos e risco."
)
TOOLS = (
    ToolSpec(
        "compound",
        "Juros compostos e aportes",
        "Projeta capital nominal com aportes constantes; retorno e inflação futuros são incertos.",
        (CAPITAL, PAYMENT, RATE, PERIODS),
        PLAN,
    ),
    ToolSpec(
        "goal",
        "Aporte para uma meta",
        "Calcula o aporte periódico necessário para um objetivo, com hipótese explícita de retorno.",
        (
            field(
                "target",
                "Objetivo futuro (R$)",
                "Montante nominal desejado no fim do prazo.",
            ),
            CAPITAL,
            RATE,
            PERIODS,
        ),
        PLAN,
    ),
    ToolSpec(
        "retirement",
        "Aposentadoria com prazo definido",
        "Calcula capital para retiradas finitas em valores reais; não presume renda vitalícia ou longevidade garantida.",
        (
            field(
                "income",
                "Complemento mensal desejado (R$ de hoje)",
                "Renda desejada menos outras rendas estáveis, informada manualmente.",
            ),
            field(
                "retirement_months",
                "Meses de retiradas",
                "Prazo do cenário de aposentadoria, até 1200 meses.",
                "int",
            ),
            field(
                "saving_months",
                "Meses até aposentar",
                "Prazo de acumulação, até 1200 meses.",
                "int",
            ),
            CAPITAL,
            field(
                "rate",
                "Retorno real mensal (%)",
                "Taxa já descontada da inflação; não use taxa nominal aqui.",
                "percent",
            ),
        ),
        PLAN,
    ),
    ToolSpec(
        "reserve",
        "Reserva de emergência",
        "Define objetivo de reserva e cobertura de despesas. Quantidade de meses é uma escolha do usuário.",
        (
            field(
                "expenses",
                "Despesas essenciais mensais (R$)",
                "Não inclui gastos que podem ser suspensos em uma emergência.",
            ),
            field(
                "months",
                "Cobertura desejada (meses)",
                "Hipótese escolhida conforme estabilidade de renda e necessidades.",
            ),
            field(
                "reserve",
                "Reserva líquida disponível (R$)",
                "Recursos realmente disponíveis; carteira de risco não equivale a reserva líquida.",
            ),
        ),
        PLAN,
    ),
    ToolSpec(
        "household",
        "Balanço pessoal e capacidade de poupança",
        "Relaciona patrimônio, orçamento e serviço da dívida, sem misturar despesas pessoais com a carteira.",
        tuple(
            field(k, l, h)
            for k, l, h in (
                (
                    "assets",
                    "Ativos pessoais (R$)",
                    "Bens e direitos avaliados de forma consistente.",
                ),
                ("liabilities", "Dívidas pessoais (R$)", "Obrigações ainda devidas."),
                (
                    "income",
                    "Renda líquida mensal (R$)",
                    "Receitas após retenções obrigatórias.",
                ),
                (
                    "expenses",
                    "Despesas mensais (R$)",
                    "Inclua parcelas da dívida no total de despesas.",
                ),
                (
                    "installments",
                    "Parcelas de dívida por mês (R$)",
                    "Parte das despesas usada para pagar dívidas.",
                ),
            )
        ),
        PLAN,
    ),
    ToolSpec(
        "rates",
        "Taxas equivalentes, inflação e ganho real",
        "Distingue taxa nominal efetiva e poder de compra. Taxas anuais são convertidas por capitalização composta.",
        (
            field(
                "nominal",
                "Retorno nominal anual (%)",
                "Hipótese ou retorno observado no ano.",
                "percent",
            ),
            field(
                "inflation",
                "Inflação anual (%)",
                "Inflação da mesma janela do retorno nominal.",
                "percent",
            ),
        ),
        PLAN,
    ),
    ToolSpec(
        "price",
        "Dívida • sistema Price",
        "Calcula parcelas constantes; não inclui seguros, tarifas ou CET além da taxa informada.",
        (CAPITAL, RATE, PERIODS),
        PLAN,
    ),
    ToolSpec(
        "sac",
        "Dívida • sistema SAC",
        "Calcula amortização constante e parcelas decrescentes; compare com o CET da proposta real.",
        (CAPITAL, RATE, PERIODS),
        PLAN,
    ),
    ToolSpec(
        "project",
        "VPL, TIR e payback descontado",
        "Compara fluxos na mesma periodicidade. TIR é omitida quando há múltiplas mudanças de sinal.",
        (FLOWS, DISCOUNT),
        ANALYSIS,
    ),
    ToolSpec(
        "gordon",
        "Preço por Gordon",
        "Valor teórico de dividendos perpétuos com crescimento constante; extremamente sensível à diferença entre taxas.",
        (
            field(
                "dividend",
                "Dividendo esperado no próximo período (R$/ação)",
                "D1 projetado pelo usuário; não é dividendo passado ou garantido.",
            ),
            DISCOUNT,
            GROWTH,
        ),
        ANALYSIS,
    ),
    ToolSpec(
        "dcf",
        "Fluxo de caixa descontado • FCFF",
        "Desconta caixa operacional livre, soma terminal e desconta dívida líquida. Cenário manual, não previsão automática.",
        (
            field(
                "flows",
                "FCFF projetados • separados por ;",
                "Fluxos da empresa para períodos 1..n, sem t=0.",
                "series",
            ),
            DISCOUNT,
            GROWTH,
            field(
                "net_debt",
                "Dívida líquida (R$)",
                "Dívida menos caixa; pode ser negativa.",
            ),
            field(
                "shares",
                "Quantidade de ações",
                "Ações da mesma base patrimonial e moeda.",
            ),
        ),
        ANALYSIS,
    ),
    ToolSpec(
        "dupont",
        "Análise DuPont",
        "Decompõe ROE em margem líquida × giro de ativos × multiplicador do patrimônio, com contas do mesmo período.",
        tuple(
            field(
                k,
                l,
                "Mesma moeda, escala, entidade e período; valores informados manualmente.",
            )
            for k, l in (
                ("net_income", "Lucro líquido"),
                ("sales", "Receita líquida"),
                ("assets", "Ativos totais"),
                ("equity", "Patrimônio líquido"),
            )
        ),
        ANALYSIS,
    ),
    ToolSpec(
        "bond",
        "Renda fixa • preço, duration e sensibilidade",
        "Precifica título de cupom fixo por períodos iguais; sem inadimplência, impostos, indexador ou calendário de dias úteis.",
        (
            field("face", "Valor de face (R$)", "Principal pago no vencimento."),
            field(
                "coupon",
                "Cupom em dinheiro por período (R$)",
                "Pagamento periódico constante; zero para título sem cupom.",
            ),
            RATE,
            PERIODS,
            field(
                "shock",
                "Choque na taxa (pontos percentuais)",
                "Ex.: 1 significa acréscimo de um ponto percentual à taxa por período.",
                "percent",
            ),
        ),
        MARKET,
    ),
    ToolSpec(
        "capm",
        "CAPM • custo de capital",
        "Retorno exigido teórico = taxa livre de risco + beta × prêmio de mercado. Mesma periodicidade e moeda.",
        (
            field(
                "rf",
                "Taxa livre de risco anual (%)",
                "Hipótese escolhida e datada pelo usuário.",
                "percent",
            ),
            field(
                "market",
                "Retorno esperado do mercado anual (%)",
                "Expectativa, não retorno garantido.",
                "percent",
            ),
            field(
                "beta",
                "Beta",
                "Sensibilidade relativa ao benchmark; pode ser negativa.",
            ),
        ),
        ANALYSIS,
    ),
    ToolSpec(
        "leverage",
        "Alavancagem e choque de preços",
        "Simula posição comprada financiada por dívida. Alavancagem amplifica perdas e pode exigir capital adicional.",
        (
            field(
                "equity",
                "Capital próprio (R$)",
                "Patrimônio que absorve os resultados.",
            ),
            field(
                "debt", "Empréstimo (R$)", "Financiamento usado na posição comprada."
            ),
            field(
                "shock",
                "Variação do preço (%)",
                "Choque hipotético no período; não probabilidade.",
                "percent",
            ),
            field(
                "funding",
                "Custo da dívida no período (%)",
                "Juros totais do mesmo horizonte, sem inferência de contrato.",
                "percent",
            ),
        ),
        "ASA/CVM, Alavancagem em Fundos, pp.7–19 (2016); cenário simples, não limite regulatório.",
    ),
    ToolSpec(
        "liquidity",
        "Liquidez • tempo estimado de saída",
        "Estima pregões para liquidar uma posição com participação limitada no volume; não prevê slippage ou execução.",
        (
            field("quantity", "Unidades da posição", "Quantidade de ações ou cotas."),
            field(
                "volume",
                "Volume médio diário • unidades",
                "Mesma unidade da posição e janela representativa.",
            ),
            field(
                "participation",
                "Participação máxima diária (%)",
                "Fração do volume que a simulação permite negociar, entre 0 e 100%.",
                "percent",
            ),
        ),
        "Resolução CVM 121/CPC 40, riscos de liquidez e premissas; uso educacional, não demonstração de conformidade.",
    ),
    ToolSpec(
        "sensitivity",
        "Sensibilidade do patrimônio a choques",
        "Calcula impacto de choques escolhidos sobre uma exposição simples comprada; não agrega derivativos ou fatores correlacionados.",
        (
            field(
                "equity",
                "Patrimônio de referência (R$)",
                "Denominador para medir impacto sobre capital próprio.",
            ),
            field(
                "exposure",
                "Exposição comprada (R$)",
                "Valor de mercado sujeito aos choques.",
            ),
            field(
                "shocks",
                "Choques em % • separados por ;",
                "Ex.: -30; -10; 10. Cenários hipotéticos, sem probabilidades.",
                "percent_series",
            ),
        ),
        "Resolução CVM 121/CPC 40, itens 40–42: análise de sensibilidade e explicação de métodos/premissas.",
    ),
    ToolSpec(
        "call",
        "Opções • resultado de call comprada",
        "Calcula resultado no vencimento. Não precifica prêmio, volatilidade implícita, margem ou exercício antecipado.",
        tuple(
            field(k, l, h)
            for k, l, h in (
                (
                    "spot",
                    "Preço do ativo no vencimento",
                    "Cenário hipotético na moeda do contrato.",
                ),
                ("strike", "Preço de exercício", "Mesmo ativo e moeda."),
                (
                    "premium",
                    "Prêmio pago por unidade",
                    "Desembolso inicial, sem correção ou taxas.",
                ),
                (
                    "quantity",
                    "Quantidade de unidades",
                    "Número de unidades do ativo, incluindo multiplicador do contrato.",
                ),
            )
        ),
        MARKET,
    ),
    ToolSpec(
        "put",
        "Opções • resultado de put comprada",
        "Calcula proteção e resultado no vencimento de put comprada; não prevê preço ou execução.",
        tuple(
            field(k, l, h)
            for k, l, h in (
                (
                    "spot",
                    "Preço do ativo no vencimento",
                    "Cenário hipotético na moeda do contrato.",
                ),
                ("strike", "Preço de exercício", "Mesmo ativo e moeda."),
                (
                    "premium",
                    "Prêmio pago por unidade",
                    "Desembolso inicial sem correção ou taxas.",
                ),
                (
                    "quantity",
                    "Quantidade de unidades",
                    "Inclua o multiplicador do contrato.",
                ),
            )
        ),
        MARKET,
    ),
    ToolSpec(
        "tax",
        "Retorno após custos e tributo informado",
        "Simula imposto sobre ganho positivo usando alíquota manual. Não calcula obrigação tributária ou substitui regras por ativo/data.",
        (
            CAPITAL,
            field(
                "ending", "Resgate bruto (R$)", "Valor final antes de custos e tributo."
            ),
            field(
                "costs",
                "Custos totais (R$)",
                "Hipótese de custos dedutíveis do ganho neste cenário, conferida pelo usuário.",
            ),
            field(
                "tax",
                "Alíquota sobre ganho positivo (%)",
                "Premissa manual; a plataforma não afirma que a alíquota é legalmente aplicável.",
                "percent",
            ),
        ),
        PLAN,
    ),
)


class EvaluateResearchTool:
    def execute(
        self, key: str, v: dict[str, Decimal | tuple[Decimal, ...]]
    ) -> ResearchResult:
        def n(name: str) -> Decimal:
            value = v[name]
            if not isinstance(value, Decimal) or not value.is_finite():
                raise DomainValidationError("Número inválido.")
            return value

        def seq(name: str) -> tuple[Decimal, ...]:
            value = v[name]
            if (
                not isinstance(value, tuple)
                or not value
                or len(value) > 1201
                or any(not x.is_finite() for x in value)
            ):
                raise DomainValidationError("Série inválida.")
            return value

        def positive(*names: str) -> None:
            if any(n(name) <= 0 for name in names):
                raise DomainValidationError(
                    "Os denominadores e capitais indicados devem ser positivos."
                )

        def nonnegative(*names: str) -> None:
            if any(n(name) < 0 for name in names):
                raise DomainValidationError(
                    "Valores de capital, custo, quantidade e dívida não podem ser negativos."
                )

        def periods(name: str = "periods") -> int:
            x = n(name)
            if x != x.to_integral_value() or not 1 <= x <= 1200:
                raise DomainValidationError("Prazo deve ser inteiro entre 1 e 1200.")
            return int(x)

        rows = []

        def add(label: str, value: Decimal | None, unit: str, help: str) -> None:
            rows.append((label, value, unit, help))

        with localcontext(
            financial_context(
                [
                    x
                    for value in v.values()
                    for x in (value if isinstance(value, tuple) else (value,))
                ],
                count=len(v),
            )
        ):
            if key == "compound":
                result = future_value(n("capital"), n("payment"), n("rate"), periods())
                add(
                    "Capital projetado",
                    result,
                    "money",
                    "VF = capital × (1+i)^n + aporte × ((1+i)^n−1)/i. Aportes no fim do período.",
                )
                add(
                    "Total aplicado",
                    n("capital") + n("payment") * periods(),
                    "money",
                    "Capital inicial mais aportes, sem retorno.",
                )
                add(
                    "Resultado nominal do cenário",
                    result - n("capital") - n("payment") * periods(),
                    "money",
                    "Diferença entre valor projetado e recursos aplicados; não é garantia.",
                )
            elif key == "goal":
                add(
                    "Aporte periódico necessário",
                    required_payment(n("target"), n("capital"), n("rate"), periods()),
                    "money",
                    "Resolve a fórmula de valor futuro para o aporte; zero quando o capital projetado já cobre a meta.",
                )
            elif key == "retirement":
                positive("income")
                r = n("rate")
                valid_rate(r)
                months = periods("retirement_months")
                capital = n("income") * (
                    (1 - (1 + r) ** (-months)) / r if r else months
                )
                add(
                    "Capital real para as retiradas",
                    capital,
                    "money",
                    "Valor presente de retiradas mensais no fim do mês. Prazo finito e retorno real constante.",
                )
                add(
                    "Aporte real mensal até aposentar",
                    required_payment(
                        capital, n("capital"), r, periods("saving_months")
                    ),
                    "money",
                    "Cenário em reais de hoje, sem impostos, custos ou risco de longevidade além do prazo informado.",
                )
            elif key == "reserve":
                positive("expenses", "months")
                nonnegative("reserve")
                target = n("expenses") * n("months")
                add(
                    "Reserva-alvo",
                    target,
                    "money",
                    "Despesas essenciais × meses escolhidos.",
                )
                add(
                    "Cobertura atual",
                    n("reserve") / n("expenses"),
                    "months",
                    "Reserva líquida / despesas essenciais mensais.",
                )
                add(
                    "Saldo a formar",
                    max(Decimal(0), target - n("reserve")),
                    "money",
                    "Objetivo menos reserva disponível, limitado a zero.",
                )
            elif key == "household":
                positive("income")
                nonnegative("assets", "liabilities", "expenses", "installments")
                if n("installments") > n("expenses"):
                    raise DomainValidationError(
                        "Parcelas devem estar incluídas nas despesas totais."
                    )
                add(
                    "Patrimônio líquido pessoal",
                    n("assets") - n("liabilities"),
                    "money",
                    "Ativos menos dívidas. Valores informados manualmente.",
                )
                add(
                    "Poupança mensal",
                    n("income") - n("expenses"),
                    "money",
                    "Receita líquida menos despesas, incluindo parcelas.",
                )
                add(
                    "Taxa de poupança",
                    (n("income") - n("expenses")) / n("income"),
                    "ratio",
                    "Pode ser negativa quando o orçamento está deficitário.",
                )
                add(
                    "Comprometimento com parcelas",
                    n("installments") / n("income"),
                    "ratio",
                    "Parcelas mensais / renda líquida, sem limite universal de aprovação de crédito.",
                )
            elif key == "rates":
                add(
                    "Retorno real anual",
                    real_rate(n("nominal"), n("inflation")),
                    "ratio",
                    "Fisher exato: (1+retorno nominal)/(1+inflação)−1.",
                )
                valid_rate(n("nominal"))
                add(
                    "Taxa nominal equivalente mensal",
                    (1 + n("nominal")) ** (Decimal(1) / 12) - 1,
                    "ratio",
                    "Capitalização composta; não é taxa anual dividida por 12.",
                )
            elif key in {"price", "sac"}:
                payments = amortization(n("capital"), n("rate"), periods(), key.upper())
                add(
                    "Total pago",
                    sum((p.payment for p in payments), Decimal(0)),
                    "money",
                    "Soma das parcelas; modelo sem seguros, tarifas ou calendário contratual.",
                )
                add(
                    "Juros totais",
                    sum((p.interest for p in payments), Decimal(0)),
                    "money",
                    "Juros calculados sobre saldo devedor de cada período.",
                )
                for p in payments:
                    add(
                        f"Parcela {p.period} • saldo {p.balance:.2f}",
                        p.payment,
                        "money",
                        f"Juros: {p.interest:.2f}; amortização: {p.principal:.2f}. Precisão interna preservada; arredondamento contratual não simulado.",
                    )
            elif key == "project":
                flows = seq("flows")
                rate = n("discount")
                add(
                    "VPL",
                    npv(flows, rate),
                    "money",
                    "Soma CF_t/(1+i)^t incluindo investimento inicial em t=0. VPL positivo depende da taxa escolhida.",
                )
                try:
                    result = irr(flows)
                    reason = "Taxa por período que zera o VPL; não é retorno anual se os fluxos forem mensais."
                except DomainValidationError as error:
                    result = None
                    reason = str(error)
                add("TIR por período", result, "ratio", reason)
                if flows[0] >= 0:
                    raise DomainValidationError(
                        "Payback deste cenário exige investimento inicial negativo."
                    )
                total = flows[0]
                payback = None
                for i, f in enumerate(flows[1:], 1):
                    discounted = f / (1 + rate) ** i
                    if (
                        total < 0 <= total + discounted
                        and discounted > 0
                        and payback is None
                    ):
                        payback = Decimal(i - 1) - total / discounted
                    total += discounted
                add(
                    "Payback descontado",
                    payback,
                    "periods",
                    "Primeira recuperação acumulada do investimento; interpolação linear dentro do período. Não mede fluxos posteriores.",
                )
            elif key == "gordon":
                if n("discount") <= n("growth") or n("dividend") <= 0:
                    raise DomainValidationError(
                        "Gordon exige dividendo positivo e taxa de desconto maior que crescimento."
                    )
                valid_rate(n("growth"))
                valid_rate(n("discount"))
                add(
                    "Preço teórico por ação",
                    n("dividend") / (n("discount") - n("growth")),
                    "money",
                    "P = D1/(k−g). Não indicado para pagamentos instáveis ou crescimento não sustentável.",
                )
            elif key == "dcf":
                add(
                    "Valor teórico do capital próprio por ação",
                    discounted_company(
                        seq("flows"),
                        n("discount"),
                        n("growth"),
                        n("net_debt"),
                        n("shares"),
                    ),
                    "money",
                    "FCFF descontado + valor terminal − dívida líquida, dividido por ações. Terminal pode dominar o cenário; valor negativo indica passivos acima do valor operacional estimado.",
                )
            elif key == "dupont":
                positive("sales", "assets", "equity")
                for label, value, help in (
                    (
                        "Margem líquida",
                        n("net_income") / n("sales"),
                        "Lucro líquido / receita.",
                    ),
                    (
                        "Giro dos ativos",
                        n("sales") / n("assets"),
                        "Receita / ativos totais.",
                    ),
                    (
                        "Multiplicador do patrimônio",
                        n("assets") / n("equity"),
                        "Ativos / patrimônio; não é dívida líquida/EBITDA.",
                    ),
                    (
                        "ROE DuPont",
                        n("net_income") / n("equity"),
                        "Produto dos três fatores. Balanços de fim de período; comparar com bases médias exige ajuste explícito.",
                    ),
                ):
                    add(
                        label,
                        value,
                        "ratio"
                        if label in {"Margem líquida", "ROE DuPont"}
                        else "multiple",
                        help,
                    )
            elif key == "bond":
                price, duration, modified = bond_metrics(
                    n("face"), n("coupon"), n("rate"), periods()
                )
                changed = bond_metrics(
                    n("face"), n("coupon"), n("rate") + n("shock"), periods()
                )[0]
                add(
                    "Preço do título",
                    price,
                    "money",
                    "Valor presente dos cupons mais principal no vencimento.",
                )
                add(
                    "Duration Macaulay",
                    duration,
                    "periods",
                    "Média ponderada dos prazos de recebimento; unidade da taxa/cupom.",
                )
                add(
                    "Duration modificada",
                    modified,
                    "multiple",
                    "Duration Macaulay/(1+taxa). Sensibilidade local, não prazo de vencimento.",
                )
                add(
                    "Preço após choque • reprificação exata",
                    changed,
                    "money",
                    "Mesmos fluxos descontados pela taxa mais choque; não usa aproximação linear.",
                )
                add(
                    "Variação estimada pela duration",
                    -modified * n("shock"),
                    "ratio",
                    "Aproximação de primeira ordem: ΔP/P ≈ −Dmod × Δtaxa. Pode divergir em choques grandes.",
                )
            elif key == "capm":
                valid_rate(n("rf"))
                valid_rate(n("market"))
                add(
                    "Custo de capital CAPM",
                    n("rf") + n("beta") * (n("market") - n("rf")),
                    "ratio",
                    "Rf + beta × (Rm−Rf). Modelo de equilíbrio, dependente de benchmark, horizonte e prêmio esperado.",
                )
            elif key == "leverage":
                positive("equity")
                nonnegative("debt", "funding")
                if n("shock") < -1:
                    raise DomainValidationError(
                        "Preço de posição comprada não pode cair mais de 100% neste modelo."
                    )
                exposure = n("equity") + n("debt")
                pnl = exposure * n("shock") - n("debt") * n("funding")
                add(
                    "Alavancagem financeira simples",
                    exposure / n("equity"),
                    "multiple",
                    "Ativo comprado / capital próprio. Não mede notional de opções/futuros ou hedge complexo.",
                )
                add(
                    "Resultado do choque",
                    pnl,
                    "money",
                    "Exposição × variação de preço − juros da dívida.",
                )
                add(
                    "Capital próprio após choque",
                    n("equity") + pnl,
                    "money",
                    "Pode ser negativo; o cenário então implica perda além do capital inicial.",
                )
                add(
                    "Recursos adicionais para cobrir patrimônio negativo",
                    max(Decimal(0), -n("equity") - pnl),
                    "money",
                    "Não é cálculo de margem de uma corretora; garantias/regras contratuais não estão modeladas.",
                )
            elif key == "liquidity":
                positive("volume", "participation")
                nonnegative("quantity")
                if n("participation") > 1:
                    raise DomainValidationError("Participação não pode exceder 100%.")
                add(
                    "Pregões estimados",
                    n("quantity") / (n("volume") * n("participation")),
                    "periods",
                    "Quantidade/(volume médio × participação). Não garante contraparte, liquidez em crise ou preço de saída.",
                )
            elif key == "sensitivity":
                positive("equity")
                nonnegative("exposure")
                for shock in seq("shocks"):
                    if shock < -1:
                        raise DomainValidationError(
                            "Choque de ativo comprado não pode ser inferior a −100%."
                        )
                    pnl = n("exposure") * shock
                    add(
                        f"Choque {shock * 100:.2f}% • impacto {pnl / n('equity') * 100:.2f}% do patrimônio",
                        n("equity") + pnl,
                        "money",
                        "Exposição simples × choque, sem previsão de probabilidade ou compensação entre fatores.",
                    )
            elif key in {"call", "put"}:
                nonnegative("spot", "strike", "premium")
                positive("quantity")
                intrinsic = max(
                    Decimal(0),
                    n("spot") - n("strike")
                    if key == "call"
                    else n("strike") - n("spot"),
                )
                add(
                    "Resultado no vencimento",
                    (intrinsic - n("premium")) * n("quantity"),
                    "money",
                    "Payoff menos prêmio pago, vezes unidades; sem custos, juros ou impostos.",
                )
                add(
                    "Prêmio total em risco",
                    n("premium") * n("quantity"),
                    "money",
                    "Posição exclusivamente comprada: perda limitada ao prêmio, sem considerar custos.",
                )
            elif key == "tax":
                positive("capital")
                nonnegative("ending", "costs", "tax")
                if n("tax") > 1:
                    raise DomainValidationError("Alíquota deve estar entre 0% e 100%.")
                gain = n("ending") - n("capital") - n("costs")
                tax = max(Decimal(0), gain) * n("tax")
                add(
                    "Tributo hipotético",
                    tax,
                    "money",
                    "Máximo(0, resgate−capital−custos) × alíquota manual. Não aplica compensações ou isenções.",
                )
                add(
                    "Resgate líquido do cenário",
                    n("ending") - n("costs") - tax,
                    "money",
                    "Deduz custos e tributo hipotético do resgate.",
                )
                add(
                    "Retorno líquido sobre capital",
                    (gain - tax) / n("capital"),
                    "ratio",
                    "Resultado após custos/tributo dividido pelo capital inicial.",
                )
            else:
                raise DomainValidationError("Ferramenta desconhecida.")
        return ResearchResult(
            tuple(rows), next(s.description for s in TOOLS if s.key == key)
        )
