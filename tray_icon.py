import logging

import qtawesome as qta
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication

from log_viewer import LogViewer

logger = logging.getLogger(__name__)


class TrayIcon(QSystemTrayIcon):
    """Ikona w zasobniku systemowym. Kliknięcie pokazuje / ukrywa podgląd logów."""

    def __init__(self, log_viewer: LogViewer, parent=None):
        super().__init__(qta.icon("fa5s.tv", color="#88c0d0"), parent)
        self._viewer = log_viewer

        self.setToolTip("Display Daemon")
        self._build_menu()
        self.activated.connect(self._on_activated)

    def _build_menu(self) -> None:
        menu = QMenu()
        menu.addAction("Pokaż logi", self._toggle_viewer)
        menu.addSeparator()
        menu.addAction("Zakończ", QApplication.instance().quit)
        self.setContextMenu(menu)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._toggle_viewer()

    def _toggle_viewer(self) -> None:
        if self._viewer.isVisible():
            self._viewer.hide()
        else:
            self._viewer.show()
            self._viewer.raise_()
            self._viewer.activateWindow()
