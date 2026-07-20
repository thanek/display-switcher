import json
import logging
import re
import subprocess

from backends.base import Backend
from modes.enums import DisplayMode

# `wpctl status` for a list
SINK_DESKTOP = ["USB Audio Speakers"]
SINK_TV = [
    "HDA NVidia Cyfrowe stereo (HDMI)",
    "HDA NVidia Digital Stereo (HDMI)",
    "HDA NVidia Cyfrowe stereo (HDMI 2)",
    "HDA NVidia Digital Stereo (HDMI 2)"
]


class LinuxBackend(Backend):
    """Wspólna dla KDE i GNOME obsługa audio przez PipeWire (wpctl)."""

    AUDIO_SINKS = {
        DisplayMode.DESKTOP: SINK_DESKTOP,
        DisplayMode.TV: SINK_TV,
    }

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

        sink_pattern = re.compile(r"(\d+)\.\s+(.*?)\s*\[")

        for line in lines:
            if line.startswith("Audio"):
                in_audio_section = True
                continue

            if in_audio_section:
                if "Sinks:" in line:
                    in_sinks_section = True
                    continue
                if in_sinks_section and ("Sources:" in line or line.startswith("Video") or "Filters:" in line):
                    break

            if in_sinks_section:
                match = sink_pattern.search(line)
                if match:
                    sinks.append({
                        "id": match.group(1),
                        "name": match.group(2).strip(),
                    })

        return sinks

    def switch_audio(self, mode: DisplayMode):
        sinks = self._get_sinks()
        logging.debug(f"FOUND SINKS: {sinks}")
        sink_id = None
        desired_sinks = [a.lower() for a in self.AUDIO_SINKS[mode]]
        for s in sinks:
            name = s.get("name")
            if name.lower() in desired_sinks:
                sink_id = s.get("id")
                break

        if sink_id is None:
            logging.error(f"Audio sink {self.AUDIO_SINKS[mode]} not found")
            return False

        self._execute(["wpctl", "set-default", str(sink_id)])
        return True

    @staticmethod
    def _execute(command, background=False) -> subprocess.CompletedProcess:
        if background:
            subprocess.Popen(command)
            return subprocess.CompletedProcess(command, None, None)
        else:
            return subprocess.run(command, capture_output=True, text=True)
