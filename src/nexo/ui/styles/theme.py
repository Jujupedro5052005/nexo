"""Central dark theme for the Nexo presentation layer."""

BACKGROUND = "#050B16"
SIDEBAR = "#07111F"
SURFACE = "#0C1727"
SURFACE_ELEVATED = "#101D30"
BORDER = "#243247"
TEXT_PRIMARY = "#F5F7FA"
TEXT_SECONDARY = "#9AA7B8"
ACCENT = "#10C7C7"
POSITIVE = "#3DDC84"
NEGATIVE = "#FF5C6C"
WARNING = "#FFB020"
INFORMATION = "#4D7CFF"

APP_STYLE = f"""
* {{ font-family: "Inter", "Segoe UI", "Ubuntu", sans-serif; color: {TEXT_PRIMARY}; font-size: 13px; }}
QMainWindow, QWidget#AppRoot, QWidget#PageContent, QStackedWidget#PageStack, QScrollArea {{ background: {BACKGROUND}; }}
QWidget#Sidebar {{ background: {SIDEBAR}; border-right: 1px solid #152239; }}
QWidget#TopBar {{ background: {BACKGROUND}; border-bottom: 1px solid #18243A; }}
QLabel#BrandName {{ color: #FFFFFF; font-size: 21px; font-weight: 750; letter-spacing: 3px; }}
QLabel#BrandMark {{ background: {ACCENT}; border-radius: 9px; color: #031114; font-size: 14px; font-weight: 800; }}
QLabel#BrandTagline, QLabel#SidebarLabel {{ color: #718096; font-size: 11px; }}
QLabel#SidebarLabel {{ font-weight: 650; letter-spacing: 1px; }}
QPushButton#NavigationButton {{ background: transparent; border: none; border-radius: 9px; color: #8290A3; font-weight: 550; min-height: 40px; padding: 0 12px; text-align: left; }}
QPushButton#NavigationButton:hover {{ background: #0D1B2C; color: #D7E2ED; }}
QPushButton#NavigationButton:pressed {{ background: #102239; }}
QPushButton#NavigationButton:checked {{ background: #0D2935; border-left: 3px solid {ACCENT}; color: #E8FFFF; font-weight: 650; padding-left: 9px; }}
QLabel#PageTitle {{ color: {TEXT_PRIMARY}; font-size: 24px; font-weight: 720; }}
QLabel#PageSubtitle {{ color: {TEXT_SECONDARY}; font-size: 12px; }}
QLabel#SectionTitle {{ color: {TEXT_PRIMARY}; font-size: 15px; font-weight: 680; }}
QLabel#SectionSubtitle, QLabel#SecondaryText, QLabel#MetricDetail {{ color: {TEXT_SECONDARY}; font-size: 11px; }}
QFrame#Card {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 12px; }}
QFrame#ClickableCard:hover {{ background: {SURFACE_ELEVATED}; border: 1px solid #35506A; border-radius: 12px; }}
QLabel#MetricLabel {{ color: {TEXT_SECONDARY}; font-size: 11px; font-weight: 650; }}
QLabel#MetricValue {{ color: {TEXT_PRIMARY}; font-size: 21px; font-weight: 720; }}
QLabel#Positive {{ color: {POSITIVE}; font-weight: 650; }}
QLabel#Negative {{ color: {NEGATIVE}; font-weight: 650; }}
QLabel#Warning {{ color: {WARNING}; font-weight: 650; }}
QLabel#AccentText {{ color: {ACCENT}; font-weight: 650; }}
QLabel#DemoBadge, QLabel#Badge {{ background: #102F3A; border: 1px solid #16505A; border-radius: 8px; color: #72E2DF; font-size: 10px; font-weight: 650; padding: 4px 8px; }}
QLabel#SuccessBadge {{ background: #102E25; border: 1px solid #1D5942; border-radius: 8px; color: {POSITIVE}; font-size: 10px; padding: 4px 8px; }}
QLabel#WarningBadge {{ background: #302513; border: 1px solid #624619; border-radius: 8px; color: {WARNING}; font-size: 10px; padding: 4px 8px; }}
QLabel#MutedBadge {{ background: #162135; border: 1px solid #2A3951; border-radius: 8px; color: #8190A4; font-size: 10px; padding: 4px 8px; }}
QPushButton#PrimaryButton {{ background: #0EA7AA; border: none; border-radius: 8px; color: #F7FFFF; font-weight: 650; min-height: 36px; padding: 0 15px; }}
QPushButton#PrimaryButton:hover {{ background: {ACCENT}; }}
QPushButton#PrimaryButton:pressed {{ background: #099295; }}
QPushButton#SecondaryButton, QPushButton#FilterButton {{ background: {SURFACE_ELEVATED}; border: 1px solid {BORDER}; border-radius: 8px; color: #CBD5E1; min-height: 34px; padding: 0 13px; }}
QPushButton#SecondaryButton:hover, QPushButton#FilterButton:hover {{ border-color: #3B526F; background: #14243A; }}
QPushButton#FilterButton:checked {{ border-color: {ACCENT}; background: #0D3039; color: #7EE8E5; }}
QPushButton#LinkButton {{ background: transparent; border: none; color: {ACCENT}; font-weight: 650; padding: 3px; }}
QPushButton#LinkButton:hover {{ color: {ACCENT}; text-decoration: underline; }}
QPushButton#IconButton {{ background: {SURFACE_ELEVATED}; border: 1px solid {BORDER}; border-radius: 18px; min-height: 36px; min-width: 36px; }}
QPushButton#IconButton:hover {{ border-color: {ACCENT}; background: #12303C; }}
QPushButton#QuickAction {{ background: {SURFACE_ELEVATED}; border: 1px solid {BORDER}; border-radius: 9px; color: #DCE6F1; min-height: 52px; padding: 0 12px; text-align: left; }}
QPushButton#QuickAction:hover {{ border-color: {ACCENT}; background: #112B38; }}
QPushButton:disabled {{ background: #101826; border-color: #1B293D; color: #56647A; }}
QComboBox, QLineEdit, QDateEdit, QDoubleSpinBox, QTextEdit {{ background: #0A1423; border: 1px solid {BORDER}; border-radius: 7px; color: #E8EEF5; min-height: 34px; padding: 0 11px; selection-background-color: #14505A; }}
QTextEdit {{ padding: 9px; }}
QComboBox:hover, QLineEdit:hover, QDateEdit:hover, QDoubleSpinBox:hover {{ border-color: #3B526F; }}
QComboBox:focus, QLineEdit:focus, QDateEdit:focus, QDoubleSpinBox:focus, QTextEdit:focus {{ border-color: {ACCENT}; }}
QComboBox::drop-down, QDateEdit::drop-down {{ border: none; width: 26px; }}
QComboBox QAbstractItemView {{ background: {SURFACE_ELEVATED}; border: 1px solid {BORDER}; selection-background-color: #16404A; outline: none; }}
QMenu {{ background: {SURFACE_ELEVATED}; border: 1px solid {BORDER}; padding: 6px; }}
QMenu::item {{ border-radius: 5px; padding: 7px 22px; }}
QMenu::item:selected {{ background: #16404A; color: #E8FFFF; }}
QCheckBox, QRadioButton {{ color: #CDD7E3; spacing: 8px; }}
QTableWidget {{ background: transparent; alternate-background-color: #0E1A2B; border: none; gridline-color: #1C2A40; selection-background-color: #123B48; }}
QTableWidget::item {{ border-bottom: 1px solid #1B293D; padding: 8px; }}
QHeaderView::section {{ background: #0A1423; border: none; border-bottom: 1px solid {BORDER}; color: #8391A5; font-size: 10px; font-weight: 650; padding: 8px; }}
QProgressBar {{ background: #152136; border: none; border-radius: 4px; min-height: 8px; max-height: 8px; text-align: center; }}
QProgressBar::chunk {{ background: {ACCENT}; border-radius: 4px; }}
QScrollBar:vertical {{ background: transparent; margin: 3px; width: 8px; }}
QScrollBar::handle:vertical {{ background: #26364D; border-radius: 4px; min-height: 30px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QDialog {{ background: {BACKGROUND}; }}
QDialog QLabel#DialogTitle {{ font-size: 20px; font-weight: 720; }}
QDialogButtonBox QPushButton {{ min-height: 36px; padding: 0 16px; }}
QToolTip {{ background: #17243A; border: 1px solid #334660; color: #EEF4FA; padding: 6px; }}
"""
