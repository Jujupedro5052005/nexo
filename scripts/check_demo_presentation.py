"""Explicit native UI check using real providers, never invoked by pytest.

No seed reset, polling of APIs or manufactured quotes. Opening the demo values
16 distinct symbols once; two asset panels add up to two history/dividend queries
each. Existing soft budgets and shared cache remain in force.
"""

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from time import monotonic

from PySide6.QtCore import QTimer

from nexo.domain.models.asset import Asset
from nexo.domain.models.market_data import AssetSearchResult
from nexo.infrastructure.database.session import default_database_path
from nexo.infrastructure.market_data.config import MarketSettings
from nexo.infrastructure.market_data.policy import ProviderUsage
from nexo.main import create_application
from nexo.main import main as start_nexo
from nexo.ui.financial_formatting import replace_rows
from nexo.ui.windows.main_window import MainWindow


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--online", action="store_true", help="Autorizar consultas reais pelos providers")
    parser.add_argument("--output", type=Path, default=Path("tmp/demo_presentation"))
    args = parser.parse_args()
    if not args.online:
        parser.error("Esta verificação acessa providers reais; utilize --online. O seed e pytest são offline.")
    args.output.mkdir(parents=True, exist_ok=True)
    settings = MarketSettings.from_environment()
    usage = ProviderUsage(default_database_path().parent / "provider_usage.json", {
        "brapi": settings.brapi_budget, "bolsai": settings.bolsai_budget,
        "Yahoo Finance": settings.yahoo_budget, "CVM": settings.cvm_budget,
    })
    before = {name: usage.count(name) for name in usage.budgets}
    normal = default_database_path()
    original = hashlib.sha256(normal.read_bytes()).hexdigest() if normal.exists() else None
    application = create_application()
    report = {"portfolios": [], "assets": {}, "pages": [], "errors": []}
    state = {"phase": "market", "index": 0}
    started = monotonic()
    timer = QTimer()
    timer.setInterval(100)

    def finish(window):
        timer.stop()
        report["requests_consumed"] = {
            name: usage.count(name) - before[name] for name in before
        }
        current = hashlib.sha256(normal.read_bytes()).hexdigest() if normal.exists() else None
        report["normal_database_unchanged"] = original == current
        (args.output / "report.json").write_text(
            json.dumps(report, default=str, ensure_ascii=False, indent=2), encoding="utf8"
        )
        print(json.dumps({"requests_consumed": report["requests_consumed"],
                          "normal_database_unchanged": original == current,
                          "errors": report["errors"]}, ensure_ascii=False), flush=True)
        if window is not None:
            window.close()
        application.quit()

    def probe():
        window = next((w for w in application.topLevelWidgets()
                       if isinstance(w, MainWindow) and w.isVisible()), None)
        if monotonic() - started > 180:
            report["errors"].append(f"Timeout na etapa {state['phase']}")
            finish(window)
            return
        if window is None:
            return
        try:
            if state["phase"] == "market":
                if len(window._market_values) != 3:
                    return
                quotes = {}
                for value in window._market_values.values():
                    quotes.update({p.position.asset.symbol: asdict(p.quote) if p.quote else None
                                   for p in value.positions})
                report["priority_quotes"] = {symbol: quotes.get(symbol) for symbol in
                                             ("PETR4", "ITSA4", "B3SA3", "VALE3", "WEGE3")}
                state["phase"] = "select_portfolio"
            elif state["phase"] == "select_portfolio":
                window._select_portfolio(state["index"] + 1)
                state["phase"] = "portfolio"
            elif state["phase"] == "portfolio":
                if len(window._market_values) != 3:
                    return
                identity = state["index"] + 1
                value = window._market_values[identity]
                report["portfolios"].append({
                    "id": identity, "valuation": asdict(value),
                    "positions_rows": window.portfolios_page.positions_table.rowCount(),
                    "transactions_rows": window.transactions_page.table.rowCount(),
                    "cost_value_chart": window.overview_page.valuation_chart is not None,
                    "allocation_chart": window.overview_page.concentration_panel.chart is not None,
                })
                window.show_page(0)
                window.grab().save(str(args.output / f"portfolio_{identity}.png"))
                state["index"] += 1
                state["phase"] = "select_portfolio" if state["index"] < 3 else "pages"
            elif state["phase"] == "pages":
                for index in range(window.page_stack.count()):
                    window.show_page(index)
                    report["pages"].append(window.page_title.text())
                window.show_page(0)
                window.grab().save(str(args.output / "dashboard.png"))
                window.show_page(7)
                comparison = window.analysis_page.comparison_panel
                for index in range(comparison.portfolios.count()):
                    comparison.portfolios.item(index).setSelected(True)
                comparison.compare()
                state["phase"] = "comparison"
                state["index"] = 0
                print("Carteiras e dez telas verificadas; comparando carteiras.", flush=True)
            elif state["phase"] == "comparison":
                panel = window.analysis_page.comparison_panel
                if len(panel.comparison) != 3:
                    return
                report["comparison"] = {"portfolios": 3, "positions_rows": panel.positions_table.rowCount(),
                                        "chart": panel.chart is not None}
                window.analysis_page.tabs.setCurrentIndex(1)
                window.grab().save(str(args.output / "comparison.png"))
                state["phase"] = "select_asset"
            elif state["phase"] == "select_asset":
                symbol = ("PETR4", "B3SA3")[state["index"]]
                window.show_page(2)
                page = window.assets_page
                page.table.clearSelection()
                page._clear_selection()
                page.results = (AssetSearchResult(Asset(symbol), symbol, "BRL"),)
                replace_rows(page.table, [(symbol, symbol, "BRL", "")])
                page.analysis_panel.yield_input.setText("6")
                page.table.selectRow(0)
                state["phase"] = "asset"
                print(f"Consultando análise real de {symbol}.", flush=True)
            elif state["phase"] == "asset":
                page = window.assets_page
                analysis = page.analysis_panel.analysis
                if analysis is None or page.runner.pool.activeThreadCount():
                    return
                symbol = analysis.asset.symbol
                report["assets"][symbol] = {
                    "analysis": asdict(analysis), "history_chart": page.chart is not None,
                    "valuation_chart": page.analysis_panel.chart is not None,
                    "history_points": len(page.history.points) if page.history else 0,
                    "dividend_events": len(analysis.dividends.events) if analysis.dividends else 0,
                    "fundamentals_available": analysis.fundamentals is not None,
                    "company_available": bool(analysis.official and analysis.official.company),
                }
                window.grab().save(str(args.output / f"{symbol}.png"))
                state["index"] += 1
                if state["index"] == 2:
                    finish(window)
                else:
                    state["phase"] = "select_asset"
        except Exception as error:  # noqa: BLE001 -- Qt callback boundary must save diagnostics and close.
            report["errors"].append(f"{type(error).__name__}: {error}")
            finish(window)

    timer.timeout.connect(probe)
    timer.start()
    result = start_nexo(demo=True)
    return result or int(bool(report["errors"]) or not report.get("normal_database_unchanged", False))


if __name__ == "__main__":
    raise SystemExit(main())
