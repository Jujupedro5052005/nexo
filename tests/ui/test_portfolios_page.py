import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPushButton

from nexo.application.portfolio.create_portfolio import CreatePortfolio
from nexo.application.portfolio.list_portfolios import ListPortfolios
from nexo.domain.interfaces.portfolio_repository import PortfolioRepositoryError
from nexo.domain.models.portfolio import Portfolio
from nexo.infrastructure.database.repositories.portfolio_repository import (
    SqlAlchemyPortfolioRepository,
)
from nexo.infrastructure.database.session import (
    create_database_engine,
    create_session_factory,
    initialize_database,
)
from nexo.ui.dialogs.forms import PortfolioDialog
from nexo.ui.windows.main_window import MainWindow


@pytest.fixture
def window(qtbot, portfolio_repository) -> MainWindow:
    window = MainWindow(CreatePortfolio(portfolio_repository), ListPortfolios(portfolio_repository))
    qtbot.addWidget(window)
    window.show()
    window.show_page(1)
    return window


def test_empty_state_offers_creation_without_demo_portfolios(window) -> None:
    assert window.portfolios_page.empty_state.isVisible()
    assert window.portfolios_page.selection_buttons == {}
    assert window.selected_portfolio_id is None


def test_page_shows_real_portfolios_without_financial_demo_values(
    window, portfolio_repository,
) -> None:
    saved = portfolio_repository.add(Portfolio(name="Minha carteira real"))
    window.portfolios_page.reload()
    labels = [label.text() for label in window.portfolios_page.findChildren(QLabel)]
    assert "Minha carteira real" in labels
    assert "Carteira vazia" in labels
    assert not any("R$" in label or "%" in label or "demonstrativos" in label for label in labels)
    assert not window.portfolios_page.empty_state.isVisible()
    assert saved.id in window.portfolios_page.selection_buttons


def open_creation_dialog(window, qtbot) -> PortfolioDialog:
    button = next(
        b for b in window.portfolios_page.findChildren(QPushButton)
        if b.property("action") == "create_portfolio"
    )
    qtbot.mouseClick(button, Qt.MouseButton.LeftButton)
    assert isinstance(window.active_dialog, PortfolioDialog)
    return window.active_dialog


def test_creation_persists_refreshes_and_selects_by_identity(
    window, portfolio_repository, qtbot,
) -> None:
    dialog = open_creation_dialog(window, qtbot)
    dialog.name_field.setText("  Nova carteira  ")
    qtbot.mouseClick(dialog.save_button, Qt.MouseButton.LeftButton)
    saved = portfolio_repository.list_all()[0]
    assert saved.name == "Nova carteira"
    assert window.selected_portfolio_id == saved.id
    assert window.portfolios_page.selection_buttons[saved.id].isChecked()
    assert not window.portfolios_page.empty_state.isVisible()
    assert window.portfolios_page.cards.count() == 1
    assert window.active_dialog is None


def test_duplicate_names_can_be_selected_independently(window, portfolio_repository, qtbot) -> None:
    first = portfolio_repository.add(Portfolio(name="Longo Prazo"))
    second = portfolio_repository.add(Portfolio(name="Longo Prazo"))
    window.portfolios_page.reload()
    for saved in (first, second):
        qtbot.mouseClick(
            window.portfolios_page.selection_buttons[saved.id], Qt.MouseButton.LeftButton,
        )
        assert window.selected_portfolio_id == saved.id
        assert sum(b.isChecked() for b in window.portfolios_page.selection_buttons.values()) == 1
        assert f"#{saved.id}" in window.portfolios_page.selection_label.text()


@pytest.mark.parametrize("name", ["", "   "])
def test_invalid_name_keeps_dialog_open_and_does_not_add_card(
    window, portfolio_repository, qtbot, name,
) -> None:
    dialog = open_creation_dialog(window, qtbot)
    dialog.name_field.setText(name)
    qtbot.mouseClick(dialog.save_button, Qt.MouseButton.LeftButton)
    assert dialog.isVisible()
    assert dialog.feedback.isVisible()
    assert portfolio_repository.list_all() == []
    assert window.portfolios_page.cards.count() == 0
    dialog.close()


def test_storage_failure_keeps_inputs_and_has_no_false_success(
    window, portfolio_repository, qtbot, monkeypatch,
) -> None:
    def fail(_portfolio):
        raise PortfolioRepositoryError("Sensitive technical details")

    monkeypatch.setattr(portfolio_repository, "add", fail)
    dialog = open_creation_dialog(window, qtbot)
    dialog.name_field.setText("Minha carteira")
    qtbot.mouseClick(dialog.save_button, Qt.MouseButton.LeftButton)
    assert dialog.isVisible()
    assert dialog.name_field.text() == "Minha carteira"
    assert "Sensitive" not in dialog.feedback.text()
    assert dialog.save_button.isEnabled()
    assert portfolio_repository.list_all() == []
    assert window.portfolios_page.cards.count() == 0
    assert window.selected_portfolio_id is None
    dialog.close()


def test_read_failure_preserves_existing_cards_and_shows_retry(
    window, portfolio_repository, monkeypatch,
) -> None:
    saved = portfolio_repository.add(Portfolio(name="Existente"))
    window.portfolios_page.reload()

    def fail():
        raise PortfolioRepositoryError("Sensitive technical details")

    monkeypatch.setattr(portfolio_repository, "list_all", fail)
    assert window.portfolios_page.reload() is False
    assert saved.id in window.portfolios_page.selection_buttons
    assert window.portfolios_page.feedback.isVisible()
    assert "Sensitive" not in window.portfolios_page.feedback.text()


def test_cancel_does_not_create_portfolio(window, portfolio_repository, qtbot) -> None:
    dialog = open_creation_dialog(window, qtbot)
    dialog.name_field.setText("Não salvar")
    dialog.reject()
    assert portfolio_repository.list_all() == []


def test_ui_creation_survives_reopening_with_a_new_repository(tmp_path, qtbot) -> None:
    path = tmp_path / "ui.db"
    engine = create_database_engine(path)
    initialize_database(engine)
    repository = SqlAlchemyPortfolioRepository(create_session_factory(engine))
    first_window = MainWindow(CreatePortfolio(repository), ListPortfolios(repository))
    qtbot.addWidget(first_window)
    first_window.show()
    first_window.show_page(1)
    try:
        dialog = open_creation_dialog(first_window, qtbot)
        dialog.name_field.setText("Persistida pela interface")
        qtbot.mouseClick(dialog.save_button, Qt.MouseButton.LeftButton)
        saved_id = first_window.selected_portfolio_id
        assert saved_id is not None
    finally:
        first_window.close()
        engine.dispose()

    reopened_engine = create_database_engine(path)
    reopened_repository = SqlAlchemyPortfolioRepository(create_session_factory(reopened_engine))
    second_window = MainWindow(CreatePortfolio(reopened_repository), ListPortfolios(reopened_repository))
    qtbot.addWidget(second_window)
    second_window.show()
    second_window.show_page(1)
    try:
        assert saved_id in second_window.portfolios_page.selection_buttons
        assert second_window.selected_portfolio_id is None
        qtbot.mouseClick(
            second_window.portfolios_page.selection_buttons[saved_id], Qt.MouseButton.LeftButton,
        )
        assert second_window.selected_portfolio_id == saved_id
    finally:
        second_window.close()
        reopened_engine.dispose()
