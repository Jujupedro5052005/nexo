from types import SimpleNamespace

import pytest
from presentation_market import PresentationMarketData

from nexo.demo_dataset import create_demo_dataset
from nexo.domain.interfaces.market_data_provider import (
    MarketOfflineError,
    QuoteBatch,
    QuoteIssue,
)
from nexo.infrastructure.database.demo_finances import seed_demo_finances
from nexo.infrastructure.database.session import create_database_engine
from nexo.ui.windows.main_window import MainWindow


@pytest.mark.parametrize("demo", [True, False])
@pytest.mark.parametrize("available", [True, False])
def test_composed_application_modes_and_presentation_equity(
    qtbot, qapp, monkeypatch, tmp_path, demo, available
):
    import nexo.main as entry

    class RecordingProvider(PresentationMarketData):
        requests = 0

        def get_quotes(self, assets):
            self.requests += 1
            if not available:
                return QuoteBatch(
                    (),
                    tuple(
                        QuoteIssue(a, MarketOfflineError("Conexao indisponivel"))
                        for a in assets
                    ),
                )
            return super().get_quotes(assets)

    provider = RecordingProvider()
    sample = tmp_path / "nexo_demo.db"
    create_demo_dataset(sample)
    engine = create_database_engine(sample)
    try:
        seed_demo_finances(engine)
    finally:
        engine.dispose()
    if not demo:
        sample.rename(tmp_path / "nexo.db")
    monkeypatch.setenv("NEXO_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("NEXO_AI_PROVIDER", "mock")
    monkeypatch.setattr(
        entry,
        "ProviderServices",
        lambda *args: SimpleNamespace(
            yahoo=provider,
            market=provider,
            fundamentals=provider,
            dividends=provider,
            official=None,
            actions=None,
            health=lambda: (),
            close=lambda: None,
        ),
    )

    def inspect():
        window = next(
            w
            for w in qapp.topLevelWidgets()
            if isinstance(w, MainWindow) and w.isVisible()
        )
        qtbot.addWidget(window)
        try:
            for identity in (1, 2, 3):
                window._select_portfolio(identity)
                if available:
                    qtbot.waitUntil(
                        lambda: (
                            window.overview_page.equity_card.value_label.text() != "—"
                        ),
                        timeout=10000,
                    )
                else:
                    qtbot.waitUntil(lambda: provider.requests > 0, timeout=10000)
                    window.wait_for_market()
                    qapp.processEvents()
                    assert window.overview_page.equity_card.value_label.text() == "—"
                assert "R$" in window.overview_page.cash_card.value_label.text()
            # Both modes must consume the injected real-service boundary. A
            # presentation-only substitution would leave this count at zero.
            assert provider.requests > 0
            before = provider.requests
            window.refresh_market()
            qtbot.waitUntil(lambda: provider.requests > before, timeout=10000)
            if demo:
                assert window.mode_badge.text() == "Apresentação"
            window.show_page(9)
            assert window.intelligence_page.companion.avatar.isVisible()
        finally:
            window.close()
        return 0

    entry.create_application()
    monkeypatch.setattr(
        entry, "create_application", lambda: SimpleNamespace(exec=inspect)
    )
    assert entry.main(demo=demo) == 0
    assert (tmp_path / ("nexo_demo.db" if demo else "nexo.db")).exists()
    assert not (tmp_path / ("nexo.db" if demo else "nexo_demo.db")).exists()
