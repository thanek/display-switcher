import glob
import json
import logging
import subprocess

from backends.base import Backend
from modes.enums import DisplayMode

# `kscreen-doctor -o` for a list
DP = "DP-1"
HDMI = "HDMI-A-1"

# `wpctl status` for a list
SINK_DESKTOP = "USB Audio Speakers"
SINK_TV = "HDA NVidia Cyfrowe stereo (HDMI)"

modes = {
    DisplayMode.DESKTOP: {"display": DP, "audio": SINK_DESKTOP, "enabled": False},
    DisplayMode.TV: {"display": HDMI, "audio": SINK_TV, "enabled": False}
}


class LinuxBackend(Backend):

    def detect_mode(self) -> DisplayMode:
        for mode_id, mode in modes.items():
            mode["enabled"] = False

        result = self._execute(["kscreen-doctor", "-j"])
        outputs = json.loads(result.stdout)["outputs"]
        for o in outputs:
            if o["name"] == DP:
                modes[DisplayMode.DESKTOP]["enabled"] = o["connected"]
            if o["name"] == HDMI:
                modes[DisplayMode.TV]["enabled"] = o["enabled"] & o["connected"]

        for mode_id, mode in modes.items():
            if mode["enabled"]:
                return mode_id

        return None

    def switch_display(self, mode: DisplayMode):
        if mode == DisplayMode.DESKTOP:
            self._execute(["kscreen-doctor", f"output.{DP}.enable"])
            self._execute(["kscreen-doctor", f"output.{HDMI}.disable"])
        else:
            self._execute(["kscreen-doctor", f"output.{DP}.disable"])
            self._execute(["kscreen-doctor", f"output.{HDMI}.enable"])
        return True

    def switch_audio(self, mode: DisplayMode):
        result = self._execute(["pw-dump"])
        sinks = json.loads(result.stdout)
        sink_id = None
        for s in sinks:
            props = s.get("info", {}).get("props", {})
            media_class = props.get("media.class")
            if media_class and media_class.lower() != "Audio/Sink".lower():
                continue
            desc = props.get("node.description")
            if desc and desc.lower() == modes[mode]["audio"].lower():
                sink_id = s.get("id")

        if sink_id is None:
            logging.error(f"Audio sink {modes[mode]["audio"]} not found")
            return False
        else:
            self._execute(["wpctl", "set-default", str(sink_id)])
            return True

    @staticmethod
    def _execute(command, background=False) -> subprocess.CompletedProcess:
        if background:
            subprocess.Popen(command)
            return subprocess.CompletedProcess(command, None, None)
        else:
            return subprocess.run(command, capture_output=True, text=True)
