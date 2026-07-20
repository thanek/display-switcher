import json

from backends.linux import LinuxBackend
from modes.enums import DisplayMode

# `kscreen-doctor -o` for a list
DP = "DP-1"
HDMI = "HDMI-A-1"


class KdeBackend(LinuxBackend):
    """Wykrywanie i przełączanie wyświetlaczy przez kscreen-doctor (KDE Plasma)."""

    def detect_mode(self) -> DisplayMode:
        desktop_enabled = False
        tv_enabled = False

        result = self._execute(["kscreen-doctor", "-j"])
        outputs = json.loads(result.stdout)["outputs"]
        for o in outputs:
            if o["name"] == DP:
                desktop_enabled = o["connected"]
            if o["name"] == HDMI:
                tv_enabled = o["enabled"] & o["connected"]

        if desktop_enabled:
            return DisplayMode.DESKTOP
        if tv_enabled:
            return DisplayMode.TV
        return None

    def switch_display(self, mode: DisplayMode):
        if mode == DisplayMode.DESKTOP:
            self._execute(["kscreen-doctor", f"output.{DP}.enable"])
            self._execute(["kscreen-doctor", f"output.{HDMI}.disable"])
        else:
            self._execute(["kscreen-doctor", f"output.{DP}.disable"])
            self._execute(["kscreen-doctor", f"output.{HDMI}.enable"])
        return True
