"""Datei-Tools. Ueberschreibende Operationen gelten als gefaehrlich und muessen bestaetigt werden."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from tools.base import Tool, ToolResult

MAX_READ_CHARS = 5000
MAX_SEARCH_RESULTS = 20


def _resolve(path_str: str) -> Path:
    return Path(path_str).expanduser().resolve()


class SearchFilesTool(Tool):
    name = "search_files"
    description = "Sucht Dateien anhand eines Namensmusters in einem Verzeichnis (rekursiv)."
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Dateiname oder Muster, z. B. '*.txt' oder 'notizen'"},
            "directory": {"type": "string", "description": "Startverzeichnis, Standard: Home-Verzeichnis"},
        },
        "required": ["query"],
    }

    def execute(self, arguments: dict[str, Any]) -> ToolResult:
        query = str(arguments.get("query", "")).strip()
        if not query:
            return ToolResult(success=False, message="Es wurde kein Suchbegriff angegeben.")
        pattern = query if any(ch in query for ch in "*?[]") else f"*{query}*"

        directory_arg = arguments.get("directory")
        directory = _resolve(directory_arg) if directory_arg else Path.home()
        if not directory.exists() or not directory.is_dir():
            return ToolResult(success=False, message=f"Das Verzeichnis '{directory}' existiert nicht.")

        matches: list[str] = []
        try:
            for path in directory.rglob(pattern):
                matches.append(str(path))
                if len(matches) >= MAX_SEARCH_RESULTS:
                    break
        except OSError:
            return ToolResult(success=False, message="Bei der Dateisuche ist ein Fehler aufgetreten.")

        if not matches:
            return ToolResult(success=True, message="Es wurden keine passenden Dateien gefunden.", data={"matches": []})
        return ToolResult(
            success=True,
            message=f"{len(matches)} Datei(en) gefunden: " + ", ".join(matches),
            data={"matches": matches},
        )


class ReadFileTool(Tool):
    name = "read_file"
    description = "Liest den Textinhalt einer Datei (die ersten 5000 Zeichen)."
    parameters = {
        "type": "object",
        "properties": {"path": {"type": "string", "description": "Pfad zur Datei"}},
        "required": ["path"],
    }

    def execute(self, arguments: dict[str, Any]) -> ToolResult:
        path = _resolve(str(arguments.get("path", "")))
        if not path.exists() or not path.is_file():
            return ToolResult(success=False, message=f"Die Datei '{path}' wurde nicht gefunden.")
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ToolResult(success=False, message=f"Die Datei '{path}' konnte nicht gelesen werden.")

        truncated = content[:MAX_READ_CHARS]
        suffix = " (gekuerzt)" if len(content) > MAX_READ_CHARS else ""
        return ToolResult(success=True, message=truncated + suffix, data={"path": str(path)})


class CreateFileTool(Tool):
    name = "create_file"
    description = "Erstellt eine neue Textdatei mit optionalem Inhalt."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Zielpfad der Datei"},
            "content": {"type": "string", "description": "Inhalt der Datei (optional)"},
        },
        "required": ["path"],
    }

    def is_dangerous(self, arguments: dict[str, Any]) -> bool:
        path_str = str(arguments.get("path", ""))
        return bool(path_str) and _resolve(path_str).exists()

    def confirmation_message(self, arguments: dict[str, Any]) -> str:
        return f"Die Datei '{arguments.get('path')}' existiert bereits. Soll ich sie wirklich ueberschreiben?"

    def execute(self, arguments: dict[str, Any]) -> ToolResult:
        path = _resolve(str(arguments.get("path", "")))
        content = str(arguments.get("content", ""))
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        except OSError:
            return ToolResult(success=False, message=f"Die Datei '{path}' konnte nicht erstellt werden.")
        return ToolResult(success=True, message=f"Die Datei '{path}' wurde erstellt.")


class MoveFileTool(Tool):
    name = "move_file"
    description = "Verschiebt eine Datei von einem Pfad zu einem anderen."
    parameters = {
        "type": "object",
        "properties": {
            "source": {"type": "string", "description": "Quellpfad"},
            "destination": {"type": "string", "description": "Zielpfad"},
        },
        "required": ["source", "destination"],
    }

    def is_dangerous(self, arguments: dict[str, Any]) -> bool:
        dest = str(arguments.get("destination", ""))
        return bool(dest) and _resolve(dest).exists()

    def confirmation_message(self, arguments: dict[str, Any]) -> str:
        return f"Die Zieldatei '{arguments.get('destination')}' existiert bereits. Soll ich sie wirklich ueberschreiben?"

    def execute(self, arguments: dict[str, Any]) -> ToolResult:
        source = _resolve(str(arguments.get("source", "")))
        destination = _resolve(str(arguments.get("destination", "")))
        if not source.exists():
            return ToolResult(success=False, message=f"Die Quelldatei '{source}' wurde nicht gefunden.")
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))
        except OSError:
            return ToolResult(success=False, message="Die Datei konnte nicht verschoben werden.")
        return ToolResult(success=True, message=f"Die Datei wurde nach '{destination}' verschoben.")


class CopyFileTool(Tool):
    name = "copy_file"
    description = "Kopiert eine Datei von einem Pfad zu einem anderen."
    parameters = {
        "type": "object",
        "properties": {
            "source": {"type": "string", "description": "Quellpfad"},
            "destination": {"type": "string", "description": "Zielpfad"},
        },
        "required": ["source", "destination"],
    }

    def is_dangerous(self, arguments: dict[str, Any]) -> bool:
        dest = str(arguments.get("destination", ""))
        return bool(dest) and _resolve(dest).exists()

    def confirmation_message(self, arguments: dict[str, Any]) -> str:
        return f"Die Zieldatei '{arguments.get('destination')}' existiert bereits. Soll ich sie wirklich ueberschreiben?"

    def execute(self, arguments: dict[str, Any]) -> ToolResult:
        source = _resolve(str(arguments.get("source", "")))
        destination = _resolve(str(arguments.get("destination", "")))
        if not source.exists():
            return ToolResult(success=False, message=f"Die Quelldatei '{source}' wurde nicht gefunden.")
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(source), str(destination))
        except OSError:
            return ToolResult(success=False, message="Die Datei konnte nicht kopiert werden.")
        return ToolResult(success=True, message=f"Die Datei wurde nach '{destination}' kopiert.")
