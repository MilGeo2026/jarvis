"""Der Assistant orchestriert ein Gespraech: Claude aufrufen, Tools ausfuehren,
gefaehrliche Aktionen zurueckstellen und nach Bestaetigung ausfuehren."""
from __future__ import annotations

import logging
from typing import Optional

from ai.claude_client import AIServiceError, ClaudeClient, extract_text, to_plain_content
from ai.conversation import ConversationManager
from app.events import ActivityBus
from app.state import AssistantState, StateManager
from security.confirmation import PendingAction, SecurityGuard, interpret_yes_no
from tools.base import ToolRegistry

logger = logging.getLogger("jarvis.assistant")

MAX_TOOL_ITERATIONS = 5


def _describe_tool(tool_name: str) -> str:
    return tool_name.replace("_", " ").capitalize() + " ..."


class Assistant:
    """Verarbeitet eine Nutzeranfrage bis zur fertigen Antwort.

    Setzt den Zustand waehrenddessen (THINKING/EXECUTING) - der letzte
    Zustand nach einem erfolgreichen Aufruf bleibt bewusst THINKING: der
    Aufrufer (Voice-Pipeline oder GUI) entscheidet, ob als naechstes
    SPEAKING (Sprachausgabe) oder direkt STANDBY folgt.
    """

    def __init__(
        self,
        claude_client: ClaudeClient,
        tool_registry: ToolRegistry,
        conversation: ConversationManager,
        security_guard: SecurityGuard,
        state_manager: StateManager,
        activity_bus: Optional[ActivityBus] = None,
    ) -> None:
        self._claude = claude_client
        self._tools = tool_registry
        self._conversation = conversation
        self._guard = security_guard
        self._state = state_manager
        self._activity = activity_bus or ActivityBus()
        self._pending: PendingAction | None = None

    @property
    def pending_action(self) -> PendingAction | None:
        return self._pending

    def handle_text(self, user_text: str) -> str:
        self._state.set(AssistantState.THINKING)
        self._activity.publish("Verarbeite Anfrage ...")
        try:
            if self._pending is not None:
                reply = self._handle_pending_confirmation(user_text)
                if reply is not None:
                    return reply
                # Ambiguous: keine klare Ja/Nein-Antwort -> Bestaetigung verwerfen
                # und die Nachricht als neue Anfrage behandeln.
                self._pending = None

            self._conversation.add_user(user_text)
            return self._run_claude_loop()
        except AIServiceError as exc:
            logger.error("KI-Dienst-Fehler: %s", exc)
            self._state.set(AssistantState.ERROR)
            return str(exc)
        except Exception:
            logger.exception("Unerwarteter Fehler bei der Verarbeitung der Anfrage")
            self._state.set(AssistantState.ERROR)
            return "Es ist ein unerwarteter Fehler aufgetreten."

    def _handle_pending_confirmation(self, user_text: str) -> str | None:
        assert self._pending is not None
        decision = interpret_yes_no(user_text)
        if decision is True:
            return self._execute_pending()
        if decision is False:
            self._pending = None
            reply = "Alles klar, ich habe die Aktion abgebrochen."
            self._conversation.add_user(user_text)
            self._conversation.add_assistant(reply)
            self._state.set(AssistantState.STANDBY)
            return reply
        return None

    def _execute_pending(self) -> str:
        pending = self._pending
        assert pending is not None
        self._pending = None
        logger.info("Tool (nach Bestaetigung): %s", pending.tool_name)
        self._state.set(AssistantState.EXECUTING)
        self._activity.publish(_describe_tool(pending.tool_name))
        result = self._tools.execute(pending.tool_name, pending.arguments)
        self._state.set(AssistantState.THINKING)

        note = (
            f"[Systemhinweis: Der Benutzer hat die Aktion bestaetigt. "
            f"Ergebnis von '{pending.tool_name}': {result.message} "
            f"Bitte bestaetige das kurz auf Deutsch.]"
        )
        self._conversation.add_raw({"role": "user", "content": note})
        response = self._claude.send(self._conversation.get_messages())
        self._conversation.add_raw({"role": "assistant", "content": to_plain_content(response.content)})
        return extract_text(response.content) or result.message

    def _run_claude_loop(self) -> str:
        for _ in range(MAX_TOOL_ITERATIONS):
            response = self._claude.send(self._conversation.get_messages())
            self._conversation.add_raw({"role": "assistant", "content": to_plain_content(response.content)})

            tool_uses = [block for block in response.content if getattr(block, "type", None) == "tool_use"]
            if not tool_uses:
                return extract_text(response.content)

            tool_result_blocks = []
            confirmation_needed = False
            for tool_use in tool_uses:
                tool = self._tools.get(tool_use.name)
                if tool is None:
                    result_message = f"Unbekanntes Tool: {tool_use.name}"
                else:
                    dangerous, question = self._guard.evaluate(tool, tool_use.input)
                    if dangerous:
                        self._pending = PendingAction(tool_use.name, tool_use.input, question)
                        result_message = question
                        confirmation_needed = True
                    else:
                        logger.info("Tool: %s", tool_use.name)
                        self._state.set(AssistantState.EXECUTING)
                        self._activity.publish(_describe_tool(tool_use.name))
                        result_message = self._tools.execute(tool_use.name, tool_use.input).message
                        self._state.set(AssistantState.THINKING)

                tool_result_blocks.append(
                    {"type": "tool_result", "tool_use_id": tool_use.id, "content": result_message}
                )

            self._conversation.add_raw({"role": "user", "content": tool_result_blocks})

            if confirmation_needed:
                response = self._claude.send(self._conversation.get_messages())
                self._conversation.add_raw(
                    {"role": "assistant", "content": to_plain_content(response.content)}
                )
                return extract_text(response.content)

        logger.warning("Maximale Anzahl an Tool-Iterationen erreicht")
        return "Ich konnte die Anfrage leider nicht vollstaendig bearbeiten."
