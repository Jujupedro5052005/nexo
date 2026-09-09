import sys
from typing import cast

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from nexo.ui.styles.theme import APP_STYLE
from nexo.ui.windows.main_window import MainWindow


def create_application() -> QApplication:
    """Create the Qt application and configure its presentation metadata."""
    instance = QApplication.instance()
    application = (
        QApplication(sys.argv) if instance is None else cast(QApplication, instance)
    )

    QCoreApplication.setApplicationName("Nexo Invest")
    QCoreApplication.setApplicationVersion("0.1.0")
    QCoreApplication.setOrganizationName("Nexo")
    application.setStyle("Fusion")
    application.setStyleSheet(APP_STYLE)
    return application


def main() -> int:
    """Start the Nexo desktop application."""
    application = create_application()
    window = MainWindow()
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
