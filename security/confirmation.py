"""Sicherheitsmechanismus: gefaehrliche Tool-Aufruf muessen vom Benutzer bestaetigt werden.

JARVIS fuehrt gefaehrliche Aktionen nie automatisch aus. Stattdessen wird die
Ausfuehrung zurueckgestellt (PendingAction) und der Benutzer gefragt. Erst eine
klare Bestaetigung im naechsten Gespraechsschritt loest die echte Ausfuehrung aus.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from tools.base import Tool

_AFFIRMATIVE = {
    "ja", "jo", "jep", "japp", "jup", "klar", "ok", "okay", "jawohl",
    "mach das", "mach es", "bestaetigt", "bestätige", "genau", "sicher", "los", "yes",
}
_NEGATIVE = {
    "nein", "ne", "nope", "abbrechen", "stopp", "stop", "lass es",
    "nicht", "no", "lieber nicht", "auf keinen fall",
}


def interpret_yes_no(text: str) -> Optional[bool]:
    """Klassifiziert eine kurze Nutzerantwort als Zustimmung/Ablehnung, sonst None."""
    normalized = text.strip().lower().strip("!.? ")
    if not normalized:
        return None
    if normalized in _AFFIRMATIVE:
        return True
    if normalized in _NEGATIVE:
        return False
    if any(normalized.startswith(word) for word in _NEGATIVE):
        return False
    if any(normalized.startswith(word) for word in _AFFIRMATIVE):
        return True
    return None


@dataclass
class PendingAction:
    tool_name: str
    arguments: dict[str, Any]
    question: str


class SecurityGuard:
    """Entscheidet, ob ein Tool-Aufruf eine Bestaetigung benoetigt."""

    def evaluate(self, tool: Tool, arguments: dict[str, Any]) -> tuple[bool, str]:
        dangerous = tool.is_dangerous(arguments)
        question = tool.confirmation_message(arguments) if dangerous else ""
        return dangerous, question
