import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton, QStackedWidget, QWidget

from nexo.ui.dialogs.forms import (
    AlertDialog,
    AssetDialog,
    GoalDialog,
    TransactionDialog,
)
from nexo.ui.windows.main_window import MainWindow


@pytest.fixture
def window(qtbot) -> MainWindow:
    main_window = MainWindow()
    qtbot.addWidget(main_window)
    main_window.show()
    return main_window


def test_main_window_can_be_created(window: MainWindow) -> None:
    assert window.windowTitle() == "Nexo Invest"
    assert window.width() == 1440
    assert window.height() == 900


def test_sidebar_and_all_product_pages_exist(window: MainWindow) -> None:
    assert window.findChild(QWidget, "Sidebar") is not None
    stack = window.findChild(QStackedWidget, "PageStack")
    assert stack is not None
    assert stack.count() == 10
    assert [stack.widget(index).objectName() for index in range(stack.count())] == [
        "overview_page",
        "portfolios_page",
        "assets_page",
        "transactions_page",
        "planning_page",
        "goals_page",
        "alerts_page",
        "analysis_page",
        "reports_page",
        "settings_page",
    ]


def test_initial_page_is_overview(window: MainWindow) -> None:
    assert window.page_stack.currentIndex() == 0
    assert window.navigation_buttons[0].isChecked()


def test_every_sidebar_item_changes_page(window: MainWindow, qtbot) -> None:
    for index, button in enumerate(window.navigation_buttons):
        qtbot.mouseClick(button, Qt.MouseButton.LeftButton)
        assert window.page_stack.currentIndex() == index
        assert button.isChecked()
        assert sum(item.isChecked() for item in window.navigation_buttons) == 1


@pytest.mark.parametrize(
    ("dialog_key", "dialog_type"),
    [
        ("transaction", TransactionDialog),
        ("asset", AssetDialog),
        ("alert", AlertDialog),
        ("goal", GoalDialog),
    ],
)
def test_quick_actions_open_their_dialogs(
    window: MainWindow,
    qtbot,
    dialog_key: str,
    dialog_type: type,
) -> None:
    overview = window.page_stack.widget(0)
    button = next(
        item
        for item in overview.findChildren(QPushButton, "QuickAction")
        if item.property("dialogKey") == dialog_key
    )

    qtbot.mouseClick(button, Qt.MouseButton.LeftButton)

    assert isinstance(window.active_dialog, dialog_type)
    assert window.active_dialog.isVisible()
    window.active_dialog.close()


def test_transaction_alert_and_goal_dialogs_have_expected_identity(
    window: MainWindow,
) -> None:
    expected = (
        ("transaction", "transaction_dialog"),
        ("alert", "alert_dialog"),
        ("goal", "goal_dialog"),
    )
    for kind, object_name in expected:
        window.open_dialog(kind)
        assert window.active_dialog is not None
        assert window.active_dialog.objectName() == object_name
        window.active_dialog.close()
