"""Explicit online smoke. Never imported or invoked by pytest.

One Yahoo ticker history call supplies both the 1y series and event columns.
CVM is cache-only in this smoke, irrespective of configured download budget.
"""

import argparse
import json
import logging
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path

from nexo.calculations.indicators.fundamentals import dividend_window
from nexo.domain.interfaces.market_data_provider import MarketDataError
from nexo.domain.models.asset import Asset
from nexo.infrastructure.market_data.composition import ProviderServices
from nexo.infrastructure.market_data.config import MarketSettings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("tmp/providers_smoke.json"))
    args = parser.parse_args()
    print(
        "Esta verificação poderá consumir:\n2 chamadas brapi\n2 chamadas bolsai\n1 consulta Yahoo\nCVM: somente cache; zero downloads",
        flush=True,
    )
    logging.getLogger("yfinance").setLevel(logging.CRITICAL)
    settings = replace(MarketSettings.from_environment(), batch_size=1, cvm_budget=0)
    providers = ProviderServices(settings, Path(__file__).resolve().parents[1] / "data")
    before = {p: providers.usage.count(p) for p in providers.usage.budgets}
    result = {}

    def run(name, operation):
        try:
            data = operation()
            result[name] = {"status": "ok", "data": asdict(data)}
            print(f"{name}: disponível", flush=True)
            return data
        except MarketDataError as error:
            result[name] = {"status": "unavailable", "reason": str(error)}
            print(f"{name}: {error}", flush=True)
            return None

    try:
        run("B3SA3 snapshot", lambda: providers.brapi.get_quote(Asset("B3SA3")))
        run("1mo brapi", lambda: providers.brapi.get_history(Asset("PETR4"), "1mo"))
        run(
            "ITSA4 fundamentals",
            lambda: providers.bolsai.get_fundamentals(Asset("ITSA4")),
        )
        run(
            "ITSA4 identity",
            lambda: providers.bolsai.get_company_identity(Asset("ITSA4")),
        )
        asset = Asset("ITSA4")
        try:
            frame = providers.yahoo._history(asset, "history", period="1y")
            history = providers.yahoo.normalize_history(asset, "1y", frame)
            start, end = dividend_window(datetime.now(timezone.utc).date())
            dividends = providers.yahoo.normalize_dividends(asset, start, end, frame)
            result["1y Yahoo"] = {"status": "ok", "data": asdict(history)}
            result["ITSA4 dividends"] = {"status": "ok", "data": asdict(dividends)}
            print(
                f"Yahoo: {len(history.points)} pontos e {len(dividends.events)} proventos normalizados",
                flush=True,
            )
        except MarketDataError as error:
            result["Yahoo"] = {"status": "unavailable", "reason": str(error)}
            print(f"Yahoo: {error}", flush=True)
        official = providers.official.execute(asset)
        result["ITSA4 CVM cache"] = {
            "status": "ok" if official.company else "unavailable",
            "data": asdict(official),
        }
        print(
            "ITSA4 CVM cache: "
            + (
                "disponível"
                if official.company
                else "indisponível · " + " | ".join(official.issues)
            ),
            flush=True,
        )
        result["requests_consumed"] = {
            p: providers.usage.count(p) - n for p, n in before.items()
        }
        print(json.dumps(result["requests_consumed"], ensure_ascii=False), flush=True)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, default=str, ensure_ascii=False, indent=2),
            encoding="utf8",
        )
        print(f"Relatório sanitizado: {args.output}")
    finally:
        providers.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
