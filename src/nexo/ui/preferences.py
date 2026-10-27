import re
from colorsys import hls_to_rgb, rgb_to_hls

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QApplication

from nexo.ui.styles.theme import APP_STYLE


def preferences() -> QSettings:
    return QSettings("Nexo", "Nexo Invest")


def profile_name() -> str:
    return str(preferences().value("profile/name", "Usuário"))


def theme_choice() -> str:
    value = str(preferences().value("appearance/theme", "dark"))
    return value if value in {"dark", "light", "system"} else "dark"


def _light_color(match: re.Match[str]) -> str:
    value = match.group()
    channels = [int(value[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    hue, lightness, saturation = rgb_to_hls(*channels)
    # Invert neutral surfaces/text; retain semantic hues with readable contrast.
    if lightness < 0.25:
        lightness = 0.98 - lightness * 0.4
        saturation *= 0.35
    elif lightness > 0.8:
        lightness = 0.14
        saturation *= 0.6
    else:
        lightness = min(lightness, 0.36)
    rgb = hls_to_rgb(hue, lightness, saturation)
    return "#" + "".join(f"{round(channel * 255):02X}" for channel in rgb)


LIGHT_STYLE = re.sub(r"#[0-9a-fA-F]{6}\b", _light_color, APP_STYLE)


def apply_theme(choice: str | None = None) -> None:
    app = QApplication.instance()
    if not isinstance(app, QApplication):
        return
    choice = choice or theme_choice()
    light = choice == "light" or (
        choice == "system" and app.styleHints().colorScheme() == Qt.ColorScheme.Light
    )
    app.setStyleSheet(LIGHT_STYLE if light else APP_STYLE)


def select_theme(choice: str) -> None:
    preferences().setValue("appearance/theme", choice)
    apply_theme(choice)
