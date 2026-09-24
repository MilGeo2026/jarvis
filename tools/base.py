"""Basisabstraktionen fuer das Tool-System.

Jedes Tool beschreibt sich selbst (Name, Beschreibung, JSON-Schema der Parameter)
und kann optional dynamisch als "gefaehrlich" eingestuft werden (z. B. weil eine
Datei ueberschrieben wuerde). Gefaehrliche Tools werden nicht direkt ausgefuehrt,
sondern muessen ueber security.SecurityGuard bestaetigt werden.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("jarvis.tools")


@dataclass
class ToolResult:
    success: bool
    message: str
    data: dict[str, Any] | None = None


class Tool(ABC):
    name: str
    description: str
    parameters: dict[str, Any]
    dangerous: bool = False

    def is_dangerous(self, arguments: dict[str, Any]) -> bool:
        """Dynamische Gefahren-Einstufung. Standardmaessig die statische Flag."""
        return self.dangerous

    def confirmation_message(self, arguments: dict[str, Any]) -> str:
        """Frage, die dem Benutzer vor Ausfuehrung gestellt wird."""
        return f"Soll ich die Aktion '{self.name}' wirklich ausfuehren?"

    @abstractmethod
    def execute(self, arguments: dict[str, Any]) -> ToolResult: ...


class ToolRegistry:
    """Sammelt alle verfuegbaren Tools und macht sie fuer Claude und die Ausfuehrung nutzbar."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def all(self) -> list[Tool]:
        return list(self._tools.values())

    def to_anthropic_schema(self) -> list[dict[str, Any]]:
        return [
            {"name": t.name, "description": t.description, "input_schema": t.parameters}
            for t in self._tools.values()
        ]

    def execute(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        tool = self._tools.get(name)
        if tool is None:
            return ToolResult(success=False, message=f"Unbekanntes Tool: {name}")
        try:
            return tool.execute(arguments)
        except Exception:
            logger.exception("Tool '%s' ist fehlgeschlagen", name)
            return ToolResult(success=False, message="Die Aktion konnte leider nicht ausgefuehrt werden.")
