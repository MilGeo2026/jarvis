"""Dezente UI-Sounds (aktivieren, Wake Word, Bestaetigung). Ueber Konfiguration abschaltbar.

Verwendet winsound (in Windows enthalten, keine Zusatz-Assets noetig). Auf anderen
Plattformen (z. B. dieser Entwicklungscontainer) verhaelt sich der Player als No-Op.
"""
from __future__ import annotations

import logging
import threading

logger = logging.getLogger("jarvis.ui")

try:
    import winsound
except ImportError:  # pragma: no cover - nicht auf Windows
    winsound = None


class SoundPlayer:
    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled

    def _play(self, tones: list[tuple[int, int]]) -> None:
        if not self.enabled or winsound is None:
            return

        def _run() -> None:
            for frequency, duration_ms in tones:
                try:
                    winsound.Beep(frequency, duration_ms)
                except RuntimeError:
                    logger.debug("Sound konnte nicht abgespielt werden.")
                    return

        threading.Thread(target=_run, daemon=True).start()

    def play_online(self) -> None:
        """JARVIS ONLINE - aufsteigende Toenfolge beim Start."""
        self._play([(660, 90), (880, 90), (1175, 120)])

    def play_wake(self) -> None:
        """Kurzer Aktivierungston beim erkannten Wake Word."""
        self._play([(1046, 70)])

    def play_confirm(self) -> None:
        """Kurzer Bestaetigungston beim Start einer Aktion."""
        self._play([(784, 60)])
