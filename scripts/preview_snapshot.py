"""Render the previously captured, sanitized online snapshot; zero remote operations."""

import argparse
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from PySide6.QtWidgets import QApplication

from nexo.domain.models.asset import Asset
from nexo.domain.models.market_data import Quote
from nexo.ui.components.market_snapshot_panel import MarketSnapshotPanel
from nexo.ui.styles.theme import APP_STYLE


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("tmp/providers_smoke.json"))
    parser.add_argument("--output", type=Path, default=Path("tmp/B3SA3_snapshot.png"))
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf8"))["B3SA3 snapshot"]["data"]
    data["asset"] = Asset(data["asset"]["symbol"])
    for field in (
        "price",
        "change",
        "change_percent",
        "day_high",
        "day_low",
        "open",
        "previous_close",
        "market_cap",
        "latency_ms",
    ):
        data[field] = Decimal(data[field]) if data[field] is not None else None
    for field in ("retrieved_at", "market_time"):
        data[field] = datetime.fromisoformat(data[field]) if data[field] else None
    application = QApplication([])
    application.setStyle("Fusion")
    application.setStyleSheet(APP_STYLE)
    panel = MarketSnapshotPanel()
    panel.resize(1100, 520)
    panel.display(Quote(**data))
    panel.show()
    application.processEvents()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if not panel.grab().save(str(args.output)):
        raise OSError("Could not save preview")
    panel.close()
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
