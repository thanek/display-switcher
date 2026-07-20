import re
import xml.etree.ElementTree as ET
from pathlib import Path

from backends.linux import LinuxBackend
from modes.enums import DisplayMode

# `gnome-monitor-config list` for a list
DP = "DP-1"
HDMI = "HDMI-1"

_CONNECTORS = {
    DisplayMode.DESKTOP: DP,
    DisplayMode.TV: HDMI,
}

_MONITORS_XML = Path.home() / ".config" / "monitors.xml"

_MONITOR_LINE = re.compile(r"Monitor \[ (\S+) \] (ON|OFF)")
_MODE_ID = re.compile(r"\[id: '(\d+)x(\d+)@([\d.]+)'\]")


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
        connector = _CONNECTORS[mode]
        command = ["gnome-monitor-config", "set", "-L", "-M", connector, "-p"]

        profile = self._saved_profile(connector)
        if profile:
            command += ["-m", profile["mode"], "-s", profile["scale"]]

        result = self._execute(command)
        return result.returncode == 0

    def _saved_profile(self, connector: str) -> dict | None:
        saved = self._read_saved_config(connector)
        if not saved:
            return None
        mode_id = self._mode_id(connector, saved["width"], saved["height"], saved["rate"])
        if not mode_id:
            return None
        return {"mode": mode_id, "scale": saved["scale"]}

    @staticmethod
    def _read_saved_config(connector: str) -> dict | None:
        if not _MONITORS_XML.exists():
            return None
        root = ET.parse(_MONITORS_XML).getroot()
        for config in root.findall("configuration"):
            logical = config.findall("logicalmonitor")
            connectors = [lm.findtext("monitor/monitorspec/connector") for lm in logical]
            if connectors != [connector]:
                continue
            lm = logical[0]
            return {
                "width": lm.findtext("monitor/mode/width"),
                "height": lm.findtext("monitor/mode/height"),
                "rate": float(lm.findtext("monitor/mode/rate")),
                "scale": lm.findtext("scale"),
            }
        return None

    def _mode_id(self, connector: str, width: str, height: str, rate: float) -> str | None:
        result = self._execute(["gnome-monitor-config", "list"])
        best_id = None
        best_delta = None
        for line in _connector_section(result.stdout, connector):
            m = _MODE_ID.search(line)
            if not m or m.group(1) != width or m.group(2) != height:
                continue
            delta = abs(float(m.group(3)) - rate)
            if best_delta is None or delta < best_delta:
                best_delta = delta
                best_id = f"{width}x{height}@{m.group(3)}"
        return best_id


def _connector_section(listing: str, connector: str):
    active = False
    for line in listing.splitlines():
        m = _MONITOR_LINE.match(line)
        if m:
            active = m.group(1) == connector
            continue
        if active:
            yield line
