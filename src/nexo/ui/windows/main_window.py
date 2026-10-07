from collections.abc import Callable
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
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

from nexo.application.assets.analyze_asset import AnalyzeAsset
from nexo.application.assets.market_data import (
    GetAssetHistory,
    GetAssetQuote,
    SearchAssets,
)
from nexo.application.assets.market_integration import (
    GetMarketIntegrationStatus,
    TestMarketConnection,
)
from nexo.application.assets.provider_status import GetProviderHealth
from nexo.application.portfolio.compare_portfolios import ComparePortfolios
from nexo.application.portfolio.create_portfolio import CreatePortfolio
from nexo.application.portfolio.financial_summary import summarize_portfolio
from nexo.application.portfolio.list_portfolios import ListPortfolios
from nexo.application.portfolio.list_transactions import ListTransactions
from nexo.application.portfolio.load_portfolio_positions import LoadPortfolioPositions
from nexo.application.portfolio.load_portfolio_valuation import LoadPortfolioValuation
from nexo.application.portfolio.register_transaction import RegisterTransaction
from nexo.calculations.valuation.portfolio import PortfolioValuation
from nexo.domain.errors import DomainValidationError
from nexo.domain.interfaces.portfolio_repository import PortfolioRepositoryError
from nexo.domain.interfaces.transaction_repository import TransactionRepositoryError
from nexo.domain.models.portfolio import Portfolio
from nexo.domain.reconstruction import ReconstructionResult
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
from nexo.ui.workers import TaskRunner

PAGE_INFO = (
    (
        "Visão Geral",
        "Acompanhe posições, custos e resultado realizado.",
        "overview",
    ),
    ("Carteiras", "Crie e selecione suas carteiras de investimento.", "portfolio"),
    ("Ativos", "Pesquise ativos e visualize informações de mercado.", "assets"),
    (
        "Movimentações",
        "Consulte e registre o histórico financeiro das carteiras.",
        "transactions",
    ),
    (
        "Planejamento",
        "Visualize receitas, despesas e capacidade de aporte.",
        "planning",
    ),
    ("Metas", "Acompanhe objetivos financeiros e seu progresso.", "goals"),
    ("Alertas", "Monitore condições relevantes para suas estratégias.", "alerts"),
    ("Análises", "Analise ativos e compare carteiras com dados reais.", "analytics"),
    ("Relatórios", "Prepare relatórios para consulta e exportação.", "reports"),
    ("Configurações", "Gerencie preferências e informações da aplicação.", "settings"),
)


class MainWindow(QMainWindow):
    """Main application shell, global navigation and dialog host."""

    INITIAL_WIDTH = 1440
    INITIAL_HEIGHT = 900

    def __init__(
        self,
        create_portfolio: CreatePortfolio,
        list_portfolios: ListPortfolios,
        register_transaction: RegisterTransaction | None = None,
        list_transactions: ListTransactions | None = None,
        load_positions: LoadPortfolioPositions | None = None,
        *,
        load_valuation: LoadPortfolioValuation | None = None,
        search_assets: SearchAssets | None = None,
        get_quote: GetAssetQuote | None = None,
        get_history: GetAssetHistory | None = None,
        analyze_asset: AnalyzeAsset | None = None,
        compare_portfolios: ComparePortfolios | None = None,
        integration_status: GetMarketIntegrationStatus | None = None,
        test_connection: TestMarketConnection | None = None,
        provider_health: GetProviderHealth | None = None,
    ) -> None:
        super().__init__()
        self._create_portfolio = create_portfolio
        self._list_portfolios = list_portfolios
        self._register_transaction = register_transaction
        self._list_transactions = list_transactions
        self._load_positions = load_positions
        self._load_valuation = load_valuation
        self._asset_cases = (search_assets, get_quote, get_history)
        self._analyze_asset = analyze_asset
        self._compare_portfolios = compare_portfolios
        self._integration_cases = (integration_status, test_connection)
        self._provider_health = provider_health
        self.market_runner = TaskRunner(self)
        self._market_generation = 0
        self._market_key: object = None
        self._explicit_market_refresh = False
        self._market_values: dict[int, PortfolioValuation] = {}
        self.selected_portfolio_id: int | None = None
        self.portfolios_page = PortfoliosPage(list_portfolios, load_positions)
        self.portfolios_page.portfolio_selected.connect(self._select_portfolio)
        self.portfolios_page.refreshed.connect(self._portfolio_list_refreshed)
        self.setObjectName("main_window")
        self.setWindowTitle("Nexo Invest")
        self.resize(self.INITIAL_WIDTH, self.INITIAL_HEIGHT)
        self.setMinimumSize(1180, 720)
        self.active_dialog: (
            DemoFormDialog | NoticeDialog | PortfolioDialog | TransactionDialog | None
        ) = None

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
        self.overview_page = OverviewPage()
        self.transactions_page = TransactionsPage()
        self.analysis_page = AnalysisPage(
            self._analyze_asset, self._list_portfolios, self._compare_portfolios
        )
        self.assets_page = AssetsPage(
            *self._asset_cases, analyze_asset=self._analyze_asset
        )
        self.assets_page.asset_selected.connect(self.analysis_page.set_asset)
        self.assets_page.integration_requested.connect(lambda: self.show_page(9))
        self.settings_page = SettingsPage(*self._integration_cases, provider_health=self._provider_health)
        pages = (
            self.overview_page,
            self.portfolios_page,
            self.assets_page,
            self.transactions_page,
            PlanningPage(),
            GoalsPage(),
            AlertsPage(),
            self.analysis_page,
            ReportsPage(),
            self.settings_page,
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
        period.addItems(
            ("Hoje", "7 dias", "Este mês", "3 meses", "6 meses", "1 ano", "Máximo")
        )
        period.setCurrentText("Este mês")
        period.setEnabled(False)
        period.setToolTip(
            "Use os filtros da página Movimentações para o histórico local."
        )
        period.setMinimumWidth(130)
        period_label = QLabel("Período:")
        period_label.setObjectName("SecondaryText")
        layout.addWidget(period_label)
        layout.addWidget(period)
        layout.addWidget(Badge("●  Banco local", "SuccessBadge"))
        self.market_refresh = QPushButton("Atualizar mercado")
        self.market_refresh.setObjectName("SecondaryButton")
        self.market_refresh.setProperty("action", "market_refresh")
        self.market_refresh.setEnabled(self._load_valuation is not None)
        self.market_refresh.clicked.connect(self.refresh_market)
        layout.addWidget(self.market_refresh)
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
        if index == 7:
            self.analysis_page.load()
        if index == 1:
            self.portfolios_page.reload()
            self.selected_portfolio_id = self.portfolios_page.selected_portfolio_id
        if index in (0, 1, 3):
            self._refresh_financial_data()
        self.page_stack.setCurrentIndex(index)
        if index == 9:
            self.settings_page.provider_panel.refresh()
        title, subtitle, _icon_name = PAGE_INFO[index]
        self.page_title.setText(title)
        self.page_subtitle.setText(subtitle)
        for button in self.navigation_buttons:
            button.setChecked(button.page_index == index)

    def open_dialog(self, kind: str) -> None:
        if kind == "transaction":
            transaction_dialog = TransactionDialog(
                self,
                register_transaction=self._register_transaction,
                portfolio_id=self.selected_portfolio_id,
            )
            transaction_dialog.transaction_created.connect(self._transaction_created)
            transaction_dialog.finished.connect(self._portfolio_dialog_finished)
            self.active_dialog = transaction_dialog
            transaction_dialog.open()
            return
        if kind == "portfolio":
            dialog = PortfolioDialog(self._create_portfolio, self)
            dialog.portfolio_created.connect(self._portfolio_created)
            dialog.finished.connect(self._portfolio_dialog_finished)
            self.active_dialog = dialog
            dialog.open()
            return
        factories: dict[str, Callable[[], DemoFormDialog | NoticeDialog]] = {
            "asset": lambda: AssetDialog(self),
            "alert": lambda: AlertDialog(self),
            "goal": lambda: GoalDialog(self),
            "report": lambda: NoticeDialog(
                "Relatórios",
                "A geração de relatórios será conectada em uma próxima etapa.",
                self,
            ),
            "notifications": lambda: NoticeDialog(
                "Notificações",
                "As notificações serão conectadas quando alertas reais estiverem disponíveis.",
                self,
            ),
            "logout": lambda: NoticeDialog(
                "Perfil",
                "Autenticação e encerramento de sessão não fazem parte deste protótipo.",
                self,
            ),
            "notice": lambda: NoticeDialog(
                "Recurso demonstrativo",
                "Esta funcionalidade será conectada ao domínio em uma próxima etapa.",
                self,
            ),
        }
        self.active_dialog = factories.get(kind, factories["notice"])()
        self.active_dialog.open()

    def _select_portfolio(self, portfolio_id: int) -> None:
        self.portfolios_page.set_selected_portfolio(portfolio_id)
        self.selected_portfolio_id = self.portfolios_page.selected_portfolio_id
        self._refresh_financial_data()

    def _portfolio_created(self, portfolio: Portfolio) -> None:
        self.analysis_page.invalidate_portfolios()
        if self.portfolios_page.reload():
            self.portfolios_page.set_selected_portfolio(portfolio.id)
            self.selected_portfolio_id = portfolio.id
            self._refresh_financial_data()

    def _transaction_created(self, _transaction: object) -> None:
        self.analysis_page.invalidate_portfolios()
        self._market_key = None
        self.portfolios_page.reload()
        self._refresh_financial_data()

    def _refresh_financial_data(self) -> None:
        identity = self.selected_portfolio_id
        result = ReconstructionResult((), ())
        history = []
        summary = None
        count = None
        error = False
        try:
            count = len(self._list_portfolios.execute())
            if (
                identity is not None
                and self._list_transactions is not None
                and self._load_positions is not None
            ):
                history = self._list_transactions.execute(identity)
                result = self._load_positions.execute(identity)
                summary = summarize_portfolio(history, result)
        except (
            PortfolioRepositoryError,
            TransactionRepositoryError,
            DomainValidationError,
        ):
            # Never leave another portfolio's data on screen after a failed switch.
            result = ReconstructionResult((), ())
            history = []
            summary = None
            error = True
        self.transactions_page.set_data(identity, history)
        self.portfolios_page.set_financial_data(identity, result)
        self.overview_page.set_financial_data(identity, count, result, summary)
        if error:
            message = "Não foi possível carregar os dados financeiros. Tente atualizar."
            self.transactions_page.feedback.setText(message)
            self.transactions_page.feedback.show()
            self.portfolios_page.feedback.setText(message)
            self.portfolios_page.feedback.show()
            self.overview_page.context_label.setText(message)
        self._update_market(not error, tuple(item.id for item in history))

    def _portfolio_list_refreshed(self) -> None:
        if self._load_valuation is not None:
            self._load_valuation.invalidate_cache()
        self.analysis_page.invalidate_portfolios()
        self.selected_portfolio_id = self.portfolios_page.selected_portfolio_id
        self._market_key = None
        self._refresh_financial_data()

    def refresh_market(self) -> None:
        self._explicit_market_refresh = True
        if self._load_valuation is not None:
            self._load_valuation.invalidate_cache()
        self.analysis_page.invalidate_portfolios()
        self._market_key = None
        self.portfolios_page.reload()
        self._refresh_financial_data()
        self.analysis_page.asset_panel.invalidate()
        if self.page_stack.currentIndex() == 2:
            self.assets_page.refresh_asset(refresh=True)
        elif self.page_stack.currentIndex() == 7:
            if self.analysis_page.tabs.currentIndex() == 0:
                self.analysis_page.load()
            elif len(self.analysis_page.comparison_panel.selected_ids()) >= 2:
                self.analysis_page.comparison_panel.compare()

    def _apply_market(self) -> None:
        identity = self.selected_portfolio_id
        self.portfolios_page.set_market_data(self._market_values, identity)
        if identity in self._market_values:
            self.overview_page.set_market_data(self._market_values[identity])

    def _update_market(
        self, local_available: bool, history_ids: tuple[int | None, ...]
    ) -> None:
        explicit = self._explicit_market_refresh
        self._explicit_market_refresh = False
        case = self._load_valuation
        identity = self.selected_portfolio_id
        identities = self.portfolios_page.portfolio_ids
        key = (identity, identities, history_ids)
        if local_available and key == self._market_key:
            self._apply_market()
            return
        self._market_generation += 1
        generation = self._market_generation
        self._market_key = key if local_available else None
        self._market_values = {}
        message = (
            "Consultando mercado…"
            if case is not None and local_available and identities
            else "Mercado indisponível ou nenhuma carteira cadastrada."
        )
        self.portfolios_page.clear_market_data(message)
        self.overview_page.clear_market_data(message)
        if case is None or not local_available or not identities:
            return

        def completed(result: Any, error: Exception | None) -> None:
            if (
                generation != self._market_generation
                or identity != self.selected_portfolio_id
            ):
                return
            if error is not None:
                self._market_key = None
                message = "Mercado indisponível. Dados locais preservados; tente Atualizar mercado."
                self.portfolios_page.clear_market_data(message)
                self.overview_page.clear_market_data(message)
                return
            self._market_values = result
            self._apply_market()

        self.market_runner.submit(lambda: case.execute_many(identities, explicit=explicit), completed)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.market_runner.stop()
        self.assets_page.runner.stop()
        self.assets_page.analysis_panel.runner.stop()
        self.analysis_page.stop()
        self.settings_page.market_panel.runner.stop()
        super().closeEvent(event)

    def wait_for_market(self) -> None:
        self.market_runner.wait()
        self.assets_page.runner.wait()
        self.assets_page.analysis_panel.runner.wait()
        self.analysis_page.wait()
        self.settings_page.market_panel.runner.wait()

    def _portfolio_dialog_finished(self, _result: int) -> None:
        self.active_dialog = None

    def _show_profile_menu(self, anchor: QPushButton) -> None:
        menu = QMenu(self)
        menu.addAction("Perfil")
        menu.addAction("Preferências", lambda: self.show_page(9))
        menu.popup(anchor.mapToGlobal(anchor.rect().bottomLeft()))
