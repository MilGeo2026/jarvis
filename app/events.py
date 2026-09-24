"""Leichte Publish/Subscribe-Kanaele fuer Zusatzinformationen der GUI.

Getrennt von AssistantState, da Aktivitätstext und Mikrofon-Pegel rein
darstellungsbezogen sind und nichts an der Kernlogik des Assistenten aendern.
"""
from __future__ import annotations

from typing import Callable, Generic, TypeVar

T = TypeVar("T")
Listener = Callable[[T], None]


class Broadcaster(Generic[T]):
    def __init__(self, initial: T) -> None:
        self._value = initial
        self._listeners: list[Listener] = []

    @property
    def value(self) -> T:
        return self._value

    def subscribe(self, listener: Listener) -> None:
        self._listeners.append(listener)

    def unsubscribe(self, listener: Listener) -> None:
        if listener in self._listeners:
            self._listeners.remove(listener)

    def publish(self, value: T) -> None:
        self._value = value
        for listener in list(self._listeners):
            listener(value)


class ActivityBus(Broadcaster[str]):
    """Kurzer, menschenlesbarer Text zum aktuellen Zustand (erkannte Sprache, Aktion, Antwort)."""

    def __init__(self) -> None:
        super().__init__("")


class AudioLevelBus(Broadcaster[float]):
    """Normalisierter Mikrofon-Pegel (0..1) waehrend des Zuhoerens, fuer die Visualisierung."""

    def __init__(self) -> None:
        super().__init__(0.0)
