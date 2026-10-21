import itertools
from dataclasses import dataclass
from decimal import Decimal

from nexo.application.analysis.research_tools import ResearchResult
from nexo.calculations.indicators.technical import technical_indicators
from nexo.calculations.risk.market import comparative_risk, tail_risk
from nexo.domain.errors import DomainValidationError
from nexo.domain.interfaces.market_data_provider import MarketDataProvider
from nexo.domain.models.asset import Asset


@dataclass(frozen=True)
class MarketResearchResult:
    result: ResearchResult
    source: str


class AnalyzeMarketRisk:
    def __init__(self, market: MarketDataProvider) -> None:
        self.market = market

    def execute(
        self,
        symbol: str,
        benchmark: str,
        exposure: Decimal,
        confidence: Decimal,
        horizon: int,
        annual_rf: Decimal,
    ) -> MarketResearchResult:
        with self.market.refresh_context(True):
            asset = Asset(symbol)
            quote = self.market.get_quote(asset)
            if quote.currency != "BRL":
                raise DomainValidationError(
                    "Este painel calcula exposição em BRL; conversão cambial não é implícita."
                )
            history = self.market.get_history(asset, "1y")
            rows = [
                (
                    name,
                    value,
                    "number",
                    "Indicador do fechamento: médias simples; IFR14 de Wilder; Bollinger20 com dois desvios populacionais; MACD12/26 com sinal EMA9. Não determina data ou ordem de compra/venda.",
                )
                for name, value in technical_indicators(history).items()
            ]
            returns = tuple(
                b.close / a.close - 1
                for a, b in zip(history.points, history.points[1:])
            )
            risk = tail_risk(returns, exposure, confidence, horizon)
            rows += [
                (
                    "VaR histórico",
                    risk.historical_var,
                    "money",
                    "Quantil nearest-rank da perda em janelas compostas sobrepostas. Pode ser excedido; não é perda máxima.",
                ),
                (
                    "Expected Shortfall histórico",
                    risk.historical_es,
                    "money",
                    "Média das perdas iguais ou superiores ao quantil observado (inclui empates).",
                ),
                (
                    "VaR normal/paramétrico",
                    risk.normal_var,
                    "money",
                    "Exposição × max(0,z × σ × raiz(h) − média × h). Assume normalidade e escala raiz do tempo.",
                ),
                (
                    "Expected Shortfall normal",
                    risk.normal_es,
                    "money",
                    "Usa cauda da distribuição normal. Não captura por si só saltos, iliquidez, derivativos ou caudas pesadas.",
                ),
                (
                    "Volatilidade diária",
                    risk.volatility,
                    "ratio",
                    "Desvio padrão amostral dos retornos simples diários.",
                ),
                (
                    "Retornos na amostra",
                    Decimal(risk.observations),
                    "number",
                    "Amostra histórica, sem estimativa da probabilidade de insolvência.",
                ),
            ]
            notes = []
            if benchmark.strip():
                bh = self.market.get_history(Asset(benchmark), "1y")
                bq = self.market.get_quote(Asset(benchmark))
                if bq.currency != quote.currency:
                    raise DomainValidationError(
                        "Benchmark e ativo devem estar na mesma moeda; FX não é implícito."
                    )
                a = {p.timestamp.date(): p.close for p in history.points}
                b = {p.timestamp.date(): p.close for p in bh.points}
                start = max(min(a), min(b))
                end = min(max(a), max(b))
                da = {d for d in a if start <= d <= end}
                db = {d for d in b if start <= d <= end}
                if da != db or len(da) < 3:
                    notes.append(
                        "Comparação indisponível: datas de fechamento divergentes ou insuficientes; não há preenchimento ou FX artificial."
                    )
                else:
                    days = sorted(da)
                    ar = tuple(a[y] / a[x] - 1 for x, y in itertools.pairwise(days))
                    br = tuple(b[y] / b[x] - 1 for x, y in itertools.pairwise(days))
                    for name, value in comparative_risk(ar, br, annual_rf).items():
                        rows.append(
                            (
                                name.title(),
                                value,
                                "number",
                                "Covariâncias amostrais em datas coincidentes; Sharpe anualiza excesso diário por raiz de 252, Treynor usa excesso médio ×252/beta. Rf anual é convertido em diário. Benchmark de preços, sem reinvestimento de proventos.",
                            )
                        )
            return MarketResearchResult(
                ResearchResult(
                    tuple(rows),
                    "VaR/ES dependem da janela e das hipóteses. IFR e médias não são previsões. Valores de risco monetário na moeda da exposição do ativo ("
                    + quote.currency
                    + "). Apenas preços, sem dividendos reinvestidos. "
                    + " ".join(notes),
                ),
                f"{asset.symbol} • {history.source} • {len(history.points)} fechamentos • consulta {history.retrieved_at.isoformat()} • {history.points[0].timestamp.date()} a {history.points[-1].timestamp.date()} • confiança {confidence * 100}% • horizonte {horizon} pregão(ões)",
            )
