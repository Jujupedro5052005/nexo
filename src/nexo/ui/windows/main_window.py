from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from nexo.ui.components.common import Badge
from nexo.ui.components.navigation_button import NavigationButton
from nexo.ui.dialogs.forms import (
    AlertDialog,
    AssetDialog,
    DemoFormDialog,
    GoalDialog,
    NoticeDialog,
    PortfolioDialog,
    TransactionDialog,
)
from nexo.ui.icons import icon
from nexo.ui.pages.activity_planning import PlanningPage, TransactionsPage
from nexo.ui.pages.analysis_reports_settings import (
    AnalysisPage,
    ReportsPage,
    SettingsPage,
)
from nexo.ui.pages.goals_alerts import AlertsPage, GoalsPage
from nexo.ui.pages.overview_page import OverviewPage
from nexo.ui.pages.portfolio_assets import AssetsPage, PortfoliosPage

PAGE_INFO = (
    ("Visão Geral", "Acompanhe seu patrimônio e sua organização financeira.", "overview"),
    ("Carteiras", "Organize e compare suas estratégias de investimento.", "portfolio"),
    ("Ativos", "Pesquise ativos e visualize informações de mercado.", "assets"),
    ("Movimentações", "Consulte e registre o histórico financeiro das carteiras.", "transactions"),
    ("Planejamento", "Visualize receitas, despesas e capacidade de aporte.", "planning"),
    ("Metas", "Acompanhe objetivos financeiros e seu progresso.", "goals"),
    ("Alertas", "Monitore condições relevantes para suas estratégias.", "alerts"),
    ("Análises", "Explore métricas e comparações demonstrativas.", "analytics"),
    ("Relatórios", "Prepare relatórios para consulta e exportação.", "reports"),
    ("Configurações", "Gerencie preferências e informações da aplicação.", "settings"),
)


class MainWindow(QMainWindow):
    """Main application shell, global navigation and dialog host."""

    INITIAL_WIDTH = 1440
    INITIAL_HEIGHT = 900

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("main_window")
        self.setWindowTitle("Nexo Invest")
        self.resize(self.INITIAL_WIDTH, self.INITIAL_HEIGHT)
        self.setMinimumSize(1180, 720)
        self.active_dialog: DemoFormDialog | NoticeDialog | None = None

        root = QWidget()
        root.setObjectName("AppRoot")
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.page_stack = QStackedWidget()
        self.page_stack.setObjectName("PageStack")
        self._add_pages()

        main_area = QWidget()
        main_area.setObjectName("AppRoot")
        main_layout = QVBoxLayout(main_area)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self._build_topbar())
        main_layout.addWidget(self.page_stack, 1)

        root_layout.addWidget(self._build_sidebar())
        root_layout.addWidget(main_area, 1)
        self.show_page(0)

    def _add_pages(self) -> None:
        pages = (
            OverviewPage(),
            PortfoliosPage(),
            AssetsPage(),
            TransactionsPage(),
            PlanningPage(),
            GoalsPage(),
            AlertsPage(),
            AnalysisPage(),
            ReportsPage(),
            SettingsPage(),
        )
        for page in pages:
            signal = getattr(page, "dialog_requested", None)
            if signal is not None:
                signal.connect(self.open_dialog)
            self.page_stack.addWidget(page)

    def _build_topbar(self) -> QWidget:
        topbar = QWidget()
        topbar.setObjectName("TopBar")
        topbar.setFixedHeight(82)
        layout = QHBoxLayout(topbar)
        layout.setContentsMargins(28, 15, 28, 13)
        layout.setSpacing(12)
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.page_title = QLabel()
        self.page_title.setObjectName("PageTitle")
        self.page_subtitle = QLabel()
        self.page_subtitle.setObjectName("PageSubtitle")
        title_box.addWidget(self.page_title)
        title_box.addWidget(self.page_subtitle)
        layout.addLayout(title_box)
        layout.addStretch()
        period = QComboBox()
        period.setObjectName("period_selector")
        period.addItems(("Hoje", "7 dias", "Este mês", "3 meses", "6 meses", "1 ano", "Máximo"))
        period.setCurrentText("Este mês")
        period.setMinimumWidth(130)
        period.setToolTip("Período: Este mês")
        period.currentTextChanged.connect(
            lambda value: period.setToolTip(f"Período: {value}")
        )
        period_label = QLabel("Período:")
        period_label.setObjectName("SecondaryText")
        layout.addWidget(period_label)
        layout.addWidget(period)
        layout.addWidget(Badge("●  Atualizado agora", "SuccessBadge"))
        notifications = QPushButton()
        notifications.setObjectName("IconButton")
        notifications.setIcon(icon("bell", "#AAB8CA"))
        notifications.setToolTip("Notificações")
        notifications.clicked.connect(lambda: self.open_dialog("notifications"))
        layout.addWidget(notifications)
        profile = QPushButton("US")
        profile.setObjectName("IconButton")
        profile.setToolTip("Abrir perfil")
        profile.clicked.connect(lambda: self._show_profile_menu(profile))
        layout.addWidget(profile)
        return topbar

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(220)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 22, 16, 16)
        layout.setSpacing(4)
        brand = QHBoxLayout()
        mark = QLabel("N")
        mark.setObjectName("BrandMark")
        mark.setFixedSize(34, 34)
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name = QLabel("NEXO")
        name.setObjectName("BrandName")
        brand.addWidget(mark)
        brand.addWidget(name)
        brand.addStretch()
        layout.addLayout(brand)
        tagline = QLabel("Investir com clareza.")
        tagline.setObjectName("BrandTagline")
        tagline.setContentsMargins(44, 0, 0, 0)
        layout.addWidget(tagline)
        layout.addSpacing(18)
        section = QLabel("NAVEGAÇÃO")
        section.setObjectName("SidebarLabel")
        layout.addWidget(section)
        self.navigation_buttons: list[NavigationButton] = []
        for index, (label, _subtitle, icon_name) in enumerate(PAGE_INFO):
            button = NavigationButton(label, icon(icon_name), index)
            button.setProperty("pageIndex", index)
            button.clicked.connect(self._page_switcher(index))
            layout.addWidget(button)
            self.navigation_buttons.append(button)
        layout.addStretch()
        new_button = QPushButton("  +  Novo")
        new_button.setObjectName("PrimaryButton")
        new_button.setToolTip("Registrar uma nova movimentação")
        new_button.clicked.connect(lambda: self.open_dialog("transaction"))
        layout.addWidget(new_button)
        profile_row = QHBoxLayout()
        avatar = QLabel("US")
        avatar.setObjectName("BrandMark")
        avatar.setFixedSize(32, 32)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        profile_text = QVBoxLayout()
        user = QLabel("Usuário")
        user.setObjectName("SectionTitle")
        role = QLabel("Perfil")
        role.setObjectName("SidebarLabel")
        profile_text.addWidget(user)
        profile_text.addWidget(role)
        profile_row.addWidget(avatar)
        profile_row.addLayout(profile_text)
        profile_row.addStretch()
        layout.addLayout(profile_row)
        logout = QPushButton("Sair")
        logout.setObjectName("LinkButton")
        logout.setIcon(icon("logout"))
        logout.setToolTip("Autenticação ainda não implementada")
        logout.clicked.connect(lambda: self.open_dialog("logout"))
        layout.addWidget(logout, alignment=Qt.AlignmentFlag.AlignLeft)
        return sidebar

    def _page_switcher(self, index: int) -> Callable[[bool], None]:
        return lambda _checked: self.show_page(index)

    def show_page(self, index: int) -> None:
        self.page_stack.setCurrentIndex(index)
        title, subtitle, _icon_name = PAGE_INFO[index]
        self.page_title.setText(title)
        self.page_subtitle.setText(subtitle)
        for button in self.navigation_buttons:
            button.setChecked(button.page_index == index)

    def open_dialog(self, kind: str) -> None:
        factories: dict[str, Callable[[], DemoFormDialog | NoticeDialog]] = {
            "transaction": lambda: TransactionDialog(self),
            "asset": lambda: AssetDialog(self),
            "alert": lambda: AlertDialog(self),
            "goal": lambda: GoalDialog(self),
            "portfolio": lambda: PortfolioDialog(self),
            "report": lambda: NoticeDialog("Relatórios", "A geração de relatórios será conectada em uma próxima etapa.", self),
            "notifications": lambda: NoticeDialog("Notificações", "As notificações serão conectadas quando alertas reais estiverem disponíveis.", self),
            "logout": lambda: NoticeDialog("Perfil", "Autenticação e encerramento de sessão não fazem parte deste protótipo.", self),
            "notice": lambda: NoticeDialog("Recurso demonstrativo", "Esta funcionalidade será conectada ao domínio em uma próxima etapa.", self),
        }
        self.active_dialog = factories.get(kind, factories["notice"])()
        self.active_dialog.open()

    def _show_profile_menu(self, anchor: QPushButton) -> None:
        menu = QMenu(self)
        menu.addAction("Perfil")
        menu.addAction("Preferências", lambda: self.show_page(9))
        menu.popup(anchor.mapToGlobal(anchor.rect().bottomLeft()))
