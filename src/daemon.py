import time
import logging
from time import sleep

from modes.enums import DisplayMode


class DisplayDaemon:
    def __init__(self, backend, interval=1):
        self.backend = backend
        self.interval = interval

        self.current_mode = None
        self.last_detected = None

    def run(self):
        while True:
            detected = self.backend.detect_mode()
            if detected != self.last_detected:
                logging.info("Detected display: {}".format(detected.name if detected else "None"))
                self.last_detected = detected

            if detected != self.current_mode:
                logging.info(f"Switching display & audio to {detected.name}")

                for i in range(3):
                    if self.backend.switch_display(detected):
                        logging.info(f":: Successfully switched display to {detected.name} after {i+1} attempt(s)")
                        break
                    time.sleep(self.interval)

                for i in range(3):
                    if self.backend.switch_audio(detected):
                        logging.info(f":: Successfully switched audio to {detected.name} after {i+1} attempt(s)")
                        break
                    time.sleep(self.interval)
                self.current_mode = detected

            time.sleep(self.interval)
