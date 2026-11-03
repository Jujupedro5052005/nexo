from types import SimpleNamespace

import pytest

from nexo.ui.windows.main_window import MainWindow


@pytest.mark.parametrize("demo", [True, False])
def test_composed_application_modes_and_presentation_equity(
    qtbot, qapp, monkeypatch, tmp_path, demo
):
    import nexo.main as entry

    class NoNetwork:
        def get_quotes(self, *args):
            pytest.fail("Presentation must not request live market data")

        def get_integration_status(self):
            return None

    unavailable = NoNetwork()
    def services(*args):
        if demo:
            pytest.fail("Presentation must not construct live provider services")
        return SimpleNamespace(
            yahoo=unavailable, market=unavailable, fundamentals=unavailable,
            dividends=unavailable, official=None, actions=None,
            health=lambda: (), close=lambda: None,
        )

    monkeypatch.setenv("NEXO_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("NEXO_AI_PROVIDER", "mock")
    monkeypatch.setattr(
        entry,
        "ProviderServices",
        services,
    )

    def inspect():
        window = next(
            w
            for w in qapp.topLevelWidgets()
            if isinstance(w, MainWindow) and w.isVisible()
        )
        qtbot.addWidget(window)
        try:
            if demo:
                for identity in (1, 2, 3):
                    window._select_portfolio(identity)
                    qtbot.waitUntil(
                        lambda: window.overview_page.equity_card.value_label.text() != "—",
                        timeout=10000,
                    )
                    assert "R$" in window.overview_page.cash_card.value_label.text()
                assert window.mode_badge.text() == "Apresentação"
                panel = window.settings_page.market_panel
                assert panel.status.state == "presentation"
                assert not panel.test_button.isEnabled()
                assert "offline" in panel.mode_label.text()
            else:
                assert window.selected_portfolio_id is None
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

