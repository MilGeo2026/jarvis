"""Tools zum Oeffnen/Schliessen von Anwendungen und Webseiten."""
from __future__ import annotations

import platform
import subprocess
import webbrowser
from typing import Any

from tools.base import Tool, ToolResult


class OpenApplicationTool(Tool):
    name = "open_application"
    description = "Oeffnet eine Anwendung auf dem Rechner anhand ihres Namens (z. B. 'spotify', 'notepad')."
    parameters = {
        "type": "object",
        "properties": {"application": {"type": "string", "description": "Name der Anwendung"}},
        "required": ["application"],
    }

    def execute(self, arguments: dict[str, Any]) -> ToolResult:
        application = str(arguments.get("application", "")).strip()
        if not application:
            return ToolResult(success=False, message="Es wurde kein Anwendungsname angegeben.")

        system = platform.system()
        try:
            if system == "Windows":
                import os

                os.startfile(application)  # type: ignore[attr-defined]
            elif system == "Darwin":
                subprocess.Popen(["open", "-a", application])
            else:
                subprocess.Popen([application])
        except (FileNotFoundError, OSError):
            return ToolResult(success=False, message=f"Die Anwendung '{application}' wurde nicht gefunden.")

        return ToolResult(success=True, message=f"{application} wurde geoeffnet.")


class CloseApplicationTool(Tool):
    name = "close_application"
    description = "Beendet eine laufende Anwendung anhand ihres Namens."
    parameters = {
        "type": "object",
        "properties": {"application": {"type": "string", "description": "Name der Anwendung"}},
        "required": ["application"],
    }
    dangerous = True  # kann ungespeicherte Arbeit des Benutzers verwerfen

    def confirmation_message(self, arguments: dict[str, Any]) -> str:
        application = arguments.get("application", "die Anwendung")
        return f"Soll ich '{application}' wirklich beenden? Ungespeicherte Aenderungen koennten verloren gehen."

    def execute(self, arguments: dict[str, Any]) -> ToolResult:
        application = str(arguments.get("application", "")).strip()
        if not application:
            return ToolResult(success=False, message="Es wurde kein Anwendungsname angegeben.")

        system = platform.system()
        try:
            if system == "Windows":
                name = application if application.lower().endswith(".exe") else f"{application}.exe"
                result = subprocess.run(
                    ["taskkill", "/IM", name, "/F"], capture_output=True, text=True, timeout=10
                )
            else:
                result = subprocess.run(["pkill", "-f", application], capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.SubprocessError):
            return ToolResult(success=False, message=f"'{application}' konnte nicht beendet werden.")

        if result.returncode != 0:
            return ToolResult(success=False, message=f"'{application}' konnte nicht gefunden oder beendet werden.")
        return ToolResult(success=True, message=f"{application} wurde beendet.")


class OpenWebsiteTool(Tool):
    name = "open_website"
    description = "Oeffnet eine Webseite im Standardbrowser. Kann auch fuer Suchanfragen genutzt werden (z. B. YouTube-Suche)."
    parameters = {
        "type": "object",
        "properties": {"url": {"type": "string", "description": "Vollstaendige URL, z. B. https://www.youtube.com"}},
        "required": ["url"],
    }

    def execute(self, arguments: dict[str, Any]) -> ToolResult:
        url = str(arguments.get("url", "")).strip()
        if not url:
            return ToolResult(success=False, message="Es wurde keine URL angegeben.")
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        try:
            opened = webbrowser.open(url)
        except Exception:
            opened = False
        if not opened:
            return ToolResult(success=False, message=f"Die Webseite '{url}' konnte nicht geoeffnet werden.")
        return ToolResult(success=True, message=f"Die Webseite {url} wurde geoeffnet.")
