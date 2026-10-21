import itertools
from decimal import Decimal, localcontext

from nexo.calculations.precision import financial_context
from nexo.domain.models.market_data import PriceHistory


def technical_indicators(history: PriceHistory) -> dict[str, Decimal | None]:
    closes = [p.close for p in history.points]
    if not closes:
        return {}
    with localcontext(financial_context(closes, count=len(closes))):

        def sma(n: int) -> Decimal | None:
            return sum(closes[-n:], Decimal(0)) / n if len(closes) >= n else None

        def emas(n: int) -> list[Decimal]:
            if len(closes) < n:
                return []
            values = [sum(closes[:n], Decimal(0)) / n]
            alpha = Decimal(2) / (n + 1)
            for price in closes[n:]:
                values.append(alpha * price + (1 - alpha) * values[-1])
            return values

        rsi = None
        if len(closes) >= 15:
            deltas = [b - a for a, b in itertools.pairwise(closes)]
            gain = sum((max(d, Decimal(0)) for d in deltas[:14]), Decimal(0)) / 14
            loss = sum((max(-d, Decimal(0)) for d in deltas[:14]), Decimal(0)) / 14
            for delta in deltas[14:]:
                gain = (gain * 13 + max(delta, Decimal(0))) / 14
                loss = (loss * 13 + max(-delta, Decimal(0))) / 14
            rsi = (
                Decimal(50)
                if gain == loss == 0
                else Decimal(100)
                if loss == 0
                else 100 - 100 / (1 + gain / loss)
            )
        mid = sma(20)
        std = (
            (sum(((c - mid) ** 2 for c in closes[-20:]), Decimal(0)) / 20).sqrt()
            if mid is not None
            else None
        )
        fast, slow = emas(12), emas(26)
        macds = [a - b for a, b in zip(fast[-len(slow) :], slow)] if slow else []
        signal = None
        if len(macds) >= 9:
            signal = sum(macds[:9], Decimal(0)) / 9
            for value in macds[9:]:
                signal = Decimal(".2") * value + Decimal(".8") * signal
        return {
            "MM20": sma(20),
            "MM60": sma(60),
            "MM200": sma(200),
            "IFR14": rsi,
            "Bollinger inferior": mid - 2 * std
            if mid is not None and std is not None
            else None,
            "Bollinger superior": mid + 2 * std
            if mid is not None and std is not None
            else None,
            "MACD 12/26": macds[-1] if macds else None,
            "Sinal MACD 9": signal,
        }
