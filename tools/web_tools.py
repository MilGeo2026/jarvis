"""Web-Tools."""
from __future__ import annotations

import re
from typing import Any

import requests

from tools.base import Tool, ToolResult

_RESULT_PATTERN = re.compile(
    r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL
)
_TAG_PATTERN = re.compile(r"<[^>]+>")


class WebSearchTool(Tool):
    name = "web_search"
    description = "Fuehrt eine Websuche durch und liefert die wichtigsten Ergebnisse (Titel + Link)."
    parameters = {
        "type": "object",
        "properties": {"query": {"type": "string", "description": "Suchanfrage"}},
        "required": ["query"],
    }

    def execute(self, arguments: dict[str, Any]) -> ToolResult:
        query = str(arguments.get("query", "")).strip()
        if not query:
            return ToolResult(success=False, message="Es wurde keine Suchanfrage angegeben.")

        try:
            response = requests.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0 (JARVIS Assistant)"},
                timeout=8,
            )
            response.raise_for_status()
        except requests.RequestException:
            return ToolResult(success=False, message="Die Websuche ist momentan nicht erreichbar.")

        matches = _RESULT_PATTERN.findall(response.text)[:5]
        if not matches:
            return ToolResult(success=True, message="Es wurden keine Ergebnisse gefunden.", data={"results": []})

        results = []
        for href, raw_title in matches:
            title = _TAG_PATTERN.sub("", raw_title).strip()
            results.append({"title": title, "url": href})

        summary = "; ".join(f"{r['title']} ({r['url']})" for r in results)
        return ToolResult(success=True, message=summary, data={"results": results})
