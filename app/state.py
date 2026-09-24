"""Zustandsverwaltung des Assistenten (fuer GUI-Anzeige und Steuerung)."""
from __future__ import annotations

from enum import Enum
from typing import Callable


class AssistantState(str, Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    THINKING = "THINKING"
    SPEAKING = "SPEAKING"
    ERROR = "ERROR"


StateListener = Callable[[AssistantState], None]


class StateManager:
    """Haelt den aktuellen Zustand und benachrichtigt Listener (z. B. die GUI) bei Aenderung."""

    def __init__(self) -> None:
        self._state = AssistantState.IDLE
        self._listeners: list[StateListener] = []

    @property
    def state(self) -> AssistantState:
        return self._state

    def subscribe(self, listener: StateListener) -> None:
        self._listeners.append(listener)

    def unsubscribe(self, listener: StateListener) -> None:
        if listener in self._listeners:
            self._listeners.remove(listener)

    def set(self, state: AssistantState) -> None:
        self._state = state
        for listener in list(self._listeners):
            listener(state)
