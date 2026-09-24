"""Kommunikations-Tools."""
from __future__ import annotations

import logging
from typing import Any

from tools.base import Tool, ToolResult

logger = logging.getLogger("jarvis.tools")


class SendNotificationTool(Tool):
    name = "send_notification"
    description = "Zeigt eine Desktop-Benachrichtigung mit Titel und Nachricht an."
    parameters = {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Titel der Benachrichtigung"},
            "message": {"type": "string", "description": "Text der Benachrichtigung"},
        },
        "required": ["title", "message"],
    }

    def execute(self, arguments: dict[str, Any]) -> ToolResult:
        title = str(arguments.get("title", "JARVIS"))
        message = str(arguments.get("message", ""))
        try:
            from plyer import notification

            notification.notify(title=title, message=message, app_name="JARVIS", timeout=8)
        except Exception:
            logger.warning("Desktop-Benachrichtigung konnte nicht angezeigt werden, Fallback auf Log.")
            return ToolResult(success=False, message="Die Benachrichtigung konnte nicht angezeigt werden.")
        return ToolResult(success=True, message="Die Benachrichtigung wurde angezeigt.")
