"""Duenner Wrapper um die Anthropic Messages API mit Tool-Use."""
from __future__ import annotations

import logging
from typing import Any

import anthropic

from ai.prompts import SYSTEM_PROMPT
from app.config import Settings
from tools.base import ToolRegistry

logger = logging.getLogger("jarvis.ai")

MAX_TOKENS = 1024


class AIServiceError(Exception):
    """Nutzerfreundlicher Fehler, wenn Claude nicht erreichbar ist oder ein Problem meldet."""


class ClaudeClient:
    def __init__(self, settings: Settings, tool_registry: ToolRegistry) -> None:
        self._settings = settings
        self._tools = tool_registry
        self._client: anthropic.Anthropic | None = None

    def _ensure_client(self) -> anthropic.Anthropic:
        if not self._settings.anthropic_api_key:
            raise AIServiceError(
                "Ich kann den KI-Dienst momentan nicht erreichen (kein ANTHROPIC_API_KEY konfiguriert)."
            )
        if self._client is None:
            self._client = anthropic.Anthropic(api_key=self._settings.anthropic_api_key)
        return self._client

    def send(self, messages: list[dict[str, Any]]) -> Any:
        client = self._ensure_client()
        try:
            return client.messages.create(
                model=self._settings.anthropic_model,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                tools=self._tools.to_anthropic_schema(),
                messages=messages,
            )
        except anthropic.APIConnectionError as exc:
            logger.error("Verbindung zu Claude fehlgeschlagen: %s", exc)
            raise AIServiceError("Ich kann den KI-Dienst momentan nicht erreichen.") from exc
        except anthropic.RateLimitError as exc:
            logger.error("Rate-Limit bei Claude erreicht: %s", exc)
            raise AIServiceError("Der KI-Dienst ist momentan ueberlastet, bitte gleich noch einmal versuchen.") from exc
        except anthropic.APIStatusError as exc:
            logger.error("Claude API Fehler (%s): %s", exc.status_code, exc)
            raise AIServiceError("Der KI-Dienst hat einen Fehler gemeldet.") from exc
        except anthropic.AnthropicError as exc:
            logger.error("Unerwarteter Anthropic-Fehler: %s", exc)
            raise AIServiceError("Es gab ein Problem bei der Kommunikation mit dem KI-Dienst.") from exc


def to_plain_content(blocks: Any) -> list[dict[str, Any]]:
    """Wandelt Anthropic-Content-Bloecke in reine dicts um (fuer die Historie)."""
    plain: list[dict[str, Any]] = []
    for block in blocks:
        block_type = getattr(block, "type", None)
        if block_type == "text":
            plain.append({"type": "text", "text": block.text})
        elif block_type == "tool_use":
            plain.append({"type": "tool_use", "id": block.id, "name": block.name, "input": block.input})
    return plain


def extract_text(blocks: Any) -> str:
    parts = [block.text for block in blocks if getattr(block, "type", None) == "text"]
    return " ".join(part.strip() for part in parts if part.strip())
