"""Globaler Hotkey zum Ein-/Ausblenden von JARVIS, unabhaengig vom Fensterfokus."""
from __future__ import annotations

import logging

from PySide6.QtCore import QObject, Signal

logger = logging.getLogger("jarvis.ui")

try:
    from pynput import keyboard
except ImportError:  # pragma: no cover - z. B. in Umgebungen ohne Input-Backend
    keyboard = None


class GlobalHotkey(QObject):
    """Registriert eine systemweite Tastenkombination (z. B. '<ctrl>+<space>')."""

    activated = Signal()

    def __init__(self, combo: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._combo = combo
        self._listener = None

    def start(self) -> bool:
        if keyboard is None:
            logger.warning("pynput ist nicht installiert, globaler Hotkey ist deaktiviert.")
            return False
        try:
            self._listener = keyboard.GlobalHotKeys({self._combo: self._on_activated})
            self._listener.start()
        except Exception:
            logger.warning("Globaler Hotkey '%s' konnte nicht registriert werden.", self._combo)
            self._listener = None
            return False
        return True

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    def _on_activated(self) -> None:
        # Laeuft im Hintergrund-Thread von pynput; Signal-Emission ueber Threads ist threadsicher.
        self.activated.emit()
