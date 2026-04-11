import subprocess
import json
from time import sleep

from backends.base import Backend
from modes.enums import DisplayMode

device_map = {
    DisplayMode.DESKTOP: "Głośniki (Realtek USB Audio)",
    DisplayMode.TV: "SAMSUNG (NVIDIA High Definition Audio)"
}

class WindowsBackend(Backend):

    def detect_mode(self) -> DisplayMode:
        display_name = subprocess.check_output(
            ["powershell", "-Command", "(Get-DisplayInfo | Where-Object Active).DisplayName"],
            text=True
        ).strip()

        if display_name == "DELL U2717D":
            return DisplayMode.DESKTOP
        return DisplayMode.TV

    def switch_display(self, mode: DisplayMode):
        if mode == DisplayMode.DESKTOP:
            subprocess.run(
                ["DisplaySwitch.exe", "/internal"],
                creationflags=0x08000000  # CREATE_NO_WINDOW
            )
        else:
            subprocess.run(
                ["DisplaySwitch.exe", "/external"],
                creationflags=0x08000000  # CREATE_NO_WINDOW
            )

    @staticmethod
    def get_sound_device_id(name: str) -> str | None:
        sound_devices_raw = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", "c:/tools/svcl.exe /sjson"],
            encoding="utf-8-sig",
            text=True
        ).strip()
        sound_devices = json.loads(sound_devices_raw)
        for device in sound_devices:
            if device["Type"] != "Device":
                continueś
            full_name = f"{device['Name']} ({device['Device Name']})"
            print(f"Found {full_name}, (looking for {name})")
            if full_name == name:
                return device['Item ID']
        return None


    def switch_audio(self, mode: DisplayMode):
        print("Setting audio to {}".format(mode.name))

        max_retries = 3
        device_id = None
        for retries in range(max_retries):
            device_id = self.get_sound_device_id(device_map[mode])
            if device_id is not None:
                break
            sleep(1)

        if not device_id:
            print("Could not get audio device ID")
            return

        subprocess.run([
            "c:/tools/svcl.exe", "/SetDefault", device_id, "all"
        ])