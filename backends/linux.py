import json
import logging
import subprocess
import re

from backends.base import Backend
from modes.enums import DisplayMode

# `kscreen-doctor -o` for a list
DP = "DP-1"
HDMI = "HDMI-A-1"

# `wpctl status` for a list
SINK_DESKTOP = ["USB Audio Speakers"]
SINK_TV = [
    "HDA NVidia Cyfrowe stereo (HDMI)",
    "HDA NVidia Digital Stereo (HDMI)",
    "HDA NVidia Cyfrowe stereo (HDMI 2)",
    "HDA NVidia Digital Stereo (HDMI 2)"
]

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

    def _get_sinks_by_pw_dump(self):
        result = self._execute(["pw-dump"])
        sinks = json.loads(result.stdout)
        result = []
        for s in sinks:
            props = s.get("info", {}).get("props", {})
            media_class = props.get("media.class")
            if not media_class or media_class.lower() != "Audio/Sink".lower():
                continue
            desc = props.get("node.description")
            if not desc:
                continue
            result.append({
                "id": s.get("id"),
                "name": desc,
            })
        return result

    def _get_sinks(self):
        output = subprocess.check_output(["wpctl", "status"], text=True)
        lines = output.splitlines()
        sinks = []
        in_audio_section = False
        in_sinks_section = False

        # Poprawiony regex:
        # 1. Szuka liczby (ID) - \d+
        # 2. Szuka kropki i spacji - \.\s+
        # 3. Przechwytuje wszystko do momentu napotkania "[" (gdzie zaczyna się [vol:...])
        sink_pattern = re.compile(r"(\d+)\.\s+(.*?)\s*\[")

        for line in lines:
            if line.startswith("Audio"):
                in_audio_section = True
                continue

            if in_audio_section:
                if "Sinks:" in line:
                    in_sinks_section = True
                    continue
                # Jeśli wejdziemy w kolejną podsekcję (np. Sources) lub główną sekcję (Video), kończymy
                if in_sinks_section and ("Sources:" in line or line.startswith("Video") or "Filters:" in line):
                    break

            if in_sinks_section:
                match = sink_pattern.search(line)
                if match:
                    sink_id = match.group(1)
                    sink_name = match.group(2).strip()
                    sinks.append({
                        "id": sink_id,
                        "name": sink_name
                    })

        return sinks


    def switch_audio(self, mode: DisplayMode):
        sinks = self._get_sinks()
        logging.debug(f"FOUND SINKS: {sinks}")
        sink_id = None
        desired_sinks = [a.lower() for a in modes[mode]["audio"]]
        for s in sinks:
            name = s.get("name")
            if name.lower() in desired_sinks:
                sink_id = s.get("id")
                break

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
