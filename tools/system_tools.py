"""System-Tools: Informationen ueber Rechner, Uhrzeit und Datum."""
from __future__ import annotations

import platform
import socket
from datetime import datetime
from typing import Any

from tools.base import Tool, ToolResult

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None

_WEEKDAYS_DE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
_MONTHS_DE = [
    "Januar", "Februar", "Maerz", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
]


class GetSystemInformationTool(Tool):
    name = "get_system_information"
    description = "Liefert Informationen ueber das aktuelle System (Betriebssystem, CPU, Arbeitsspeicher, Hostname)."
    parameters = {"type": "object", "properties": {}, "required": []}

    def execute(self, arguments: dict[str, Any]) -> ToolResult:
        info = {
            "betriebssystem": f"{platform.system()} {platform.release()}",
            "hostname": socket.gethostname(),
            "prozessor": platform.processor() or platform.machine(),
            "python_version": platform.python_version(),
        }
        if psutil is not None:
            info["cpu_kerne"] = psutil.cpu_count(logical=True)
            info["arbeitsspeicher_gb"] = round(psutil.virtual_memory().total / (1024 ** 3), 1)

        text = ", ".join(f"{k}: {v}" for k, v in info.items())
        return ToolResult(success=True, message=text, data=info)


class GetCurrentTimeTool(Tool):
    name = "get_current_time"
    description = "Liefert die aktuelle Uhrzeit."
    parameters = {"type": "object", "properties": {}, "required": []}

    def execute(self, arguments: dict[str, Any]) -> ToolResult:
        now = datetime.now()
        text = now.strftime("%H:%M Uhr")
        return ToolResult(success=True, message=text, data={"time": now.isoformat()})


class GetCurrentDateTool(Tool):
    name = "get_current_date"
    description = "Liefert das aktuelle Datum."
    parameters = {"type": "object", "properties": {}, "required": []}

    def execute(self, arguments: dict[str, Any]) -> ToolResult:
        now = datetime.now()
        weekday = _WEEKDAYS_DE[now.weekday()]
        month = _MONTHS_DE[now.month - 1]
        text = f"{weekday}, {now.day}. {month} {now.year}"
        return ToolResult(success=True, message=text, data={"date": now.date().isoformat()})
