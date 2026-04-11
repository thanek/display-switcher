from abc import ABC, abstractmethod
from modes.enums import DisplayMode


class Backend(ABC):

    @abstractmethod
    def detect_mode(self) -> DisplayMode:
        """Zwraca aktualny tryb na podstawie hardware (DP / etc)"""

    @abstractmethod
    def switch_display(self, mode: DisplayMode) -> bool:
        """Przełącza wyświetlanie"""

    @abstractmethod
    def switch_audio(self, mode: DisplayMode) -> bool:
        """Przełącza wyjście audio"""
