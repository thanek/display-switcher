import logging

import qtawesome as qta
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication, QMessageBox

from log_viewer import LogViewer
from modes.enums import DisplayMode

logger = logging.getLogger(__name__)

_ICONS = {
    DisplayMode.TV:      ("fa5s.tv",      "#88c0d0"),
    DisplayMode.DESKTOP: ("fa5s.desktop", "#a3be8c"),
}
_ICON_DEFAULT = ("fa5s.tv", "#88c0d0")


def _make_icon(name: str, color: str):
    return qta.icon(name, color=color)


class TrayIcon(QSystemTrayIcon):
    """Ikona w zasobniku systemowym. Kliknięcie pokazuje / ukrywa podgląd logów."""

    def __init__(self, log_viewer: LogViewer, daemon, parent=None):
        super().__init__(_make_icon(*_ICON_DEFAULT), parent)
        self._viewer = log_viewer
        self._daemon = daemon
        self._known_mode = None

        self.setToolTip("Display Switcher")
        self._build_menu()
        self.activated.connect(self._on_activated)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._sync_icon)
        self._timer.start(1000)

    def _build_menu(self) -> None:
        menu = QMenu()
        menu.addAction("Pokaż logi", self._toggle_viewer)
        menu.addAction("O programie", self._show_about)
        menu.addSeparator()
        menu.addAction("Zakończ", QApplication.instance().quit)
        self.setContextMenu(menu)

    def _show_about(self) -> None:
        backend = type(self._daemon.backend).__name__
        QMessageBox.information(
            None,
            "O programie",
            f"Display Switcher\n\nBackend: {backend}",
        )

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._toggle_viewer()

    def _sync_icon(self) -> None:
        mode = self._daemon.current_mode
        if mode == self._known_mode:
            return
        self._known_mode = mode
        icon_name, color = _ICONS.get(mode, _ICON_DEFAULT)
        self.setIcon(_make_icon(icon_name, color))
        label = mode.name if mode else "?"
        self.setToolTip(f"Display Switcher — {label}")

    def _toggle_viewer(self) -> None:
        if self._viewer.isVisible():
            self._viewer.hide()
        else:
            self._viewer.show()
            self._viewer.raise_()
            self._viewer.activateWindow()
