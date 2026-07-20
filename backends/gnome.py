import re

from backends.linux import LinuxBackend
from modes.enums import DisplayMode

# `gnome-monitor-config list` for a list
DP = "DP-1"
HDMI = "HDMI-1"

_MONITOR_LINE = re.compile(r"Monitor \[ (\S+) \] (ON|OFF)")


class GnomeBackend(LinuxBackend):
    """Wykrywanie i przełączanie wyświetlaczy przez gnome-monitor-config (GNOME/Mutter)."""

    def _list_monitors(self) -> dict[str, bool]:
        result = self._execute(["gnome-monitor-config", "list"])
        monitors = {}
        for line in result.stdout.splitlines():
            m = _MONITOR_LINE.match(line)
            if m:
                monitors[m.group(1)] = m.group(2) == "ON"
        return monitors

    def detect_mode(self) -> DisplayMode:
        monitors = self._list_monitors()

        if DP in monitors:
            return DisplayMode.DESKTOP
        if monitors.get(HDMI, False):
            return DisplayMode.TV
        return None

    def switch_display(self, mode: DisplayMode):
        connector = DP if mode == DisplayMode.DESKTOP else HDMI
        result = self._execute(["gnome-monitor-config", "set", "-L", "-M", connector, "-p"])
        return result.returncode == 0
