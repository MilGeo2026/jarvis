"""Verwaltung des Gespraechskontexts fuer die Anthropic Messages API."""
from __future__ import annotations

from typing import Any


class ConversationManager:
    """Haelt den Nachrichtenverlauf und begrenzt ihn auf eine maximale Laenge.

    Die Historie wird nur an "sauberen" Grenzen gekuerzt (Beginn einer neuen
    Nutzeranfrage mit reinem Text), damit zusammengehoerige tool_use/tool_result
    Bloecke innerhalb eines Austauschs nie auseinandergerissen werden - das
    wuerde die Anthropic API mit einem Fehler ablehnen.
    """

    def __init__(self, max_messages: int = 30) -> None:
        self.max_messages = max_messages
        self._history: list[dict[str, Any]] = []

    def add_user(self, text: str) -> None:
        self._history.append({"role": "user", "content": text})
        self._trim()

    def add_assistant(self, text: str) -> None:
        self._history.append({"role": "assistant", "content": text})
        self._trim()

    def add_raw(self, message: dict[str, Any]) -> None:
        """Fuegt eine rohe Nachricht hinzu (fuer tool_use/tool_result Zwischenschritte)."""
        self._history.append(message)

    def get_messages(self) -> list[dict[str, Any]]:
        return list(self._history)

    def clear(self) -> None:
        self._history.clear()

    def _is_boundary(self, message: dict[str, Any]) -> bool:
        return message.get("role") == "user" and isinstance(message.get("content"), str)

    def _trim(self) -> None:
        while len(self._history) > self.max_messages:
            if not self._is_boundary(self._history[0]):
                break
            self._history.pop(0)
            while self._history and not self._is_boundary(self._history[0]):
                self._history.pop(0)
