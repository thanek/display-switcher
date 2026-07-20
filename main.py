import platform
import logging
import shutil
import sys
import threading
import os

from PyQt6.QtWidgets import QApplication

from daemon import DisplayDaemon
from backends.kde import KdeBackend
from backends.gnome import GnomeBackend
from backends.windows import WindowsBackend
from log_viewer import LogViewer
from tray_icon import TrayIcon

LOG_FILE = os.path.join(os.path.dirname(__file__), "display_switcher.log")
FORMAT = '%(asctime)s %(levelname)-8s %(message)s'


def _setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format=FORMAT,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
        ],
    )


def _select_linux_backend():
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").upper()
    if "KDE" in desktop:
        return KdeBackend()
    if "GNOME" in desktop:
        return GnomeBackend()
    if shutil.which("kscreen-doctor"):
        return KdeBackend()
    if shutil.which("gnome-monitor-config"):
        return GnomeBackend()
    raise RuntimeError(f"Unsupported Linux desktop environment: {desktop or '?'}")


def main():
    _setup_logging()

    if platform.system() == "Linux":
        backend = _select_linux_backend()
        logging.info(f"Using the {type(backend).__name__}")
    else:
        logging.info("Using the Windows backend")
        backend = WindowsBackend()

    daemon = DisplayDaemon(backend)

    daemon_thread = threading.Thread(target=daemon.run, daemon=True, name="DisplayDaemon")

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    viewer = LogViewer(LOG_FILE)
    tray = TrayIcon(viewer, daemon)
    tray.show()

    logging.info("Starting display switcher")
    daemon_thread.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
