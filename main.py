import platform
import logging
import sys
import threading
import os

from PyQt6.QtWidgets import QApplication

from daemon import DisplayDaemon
from backends.linux import LinuxBackend
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


def main():
    _setup_logging()

    backend_name = platform.system()
    if backend_name == "Linux":
        logging.info("Using the Linux backend")
        backend = LinuxBackend()
    else:
        logging.info("Using the Windows backend")
        backend = WindowsBackend()

    daemon = DisplayDaemon(backend)

    daemon_thread = threading.Thread(target=daemon.run, daemon=True, name="DisplayDaemon")

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    viewer = LogViewer(LOG_FILE)
    tray = TrayIcon(viewer)
    tray.show()

    logging.info("Starting display daemon")
    daemon_thread.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
