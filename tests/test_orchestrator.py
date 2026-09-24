from types import SimpleNamespace
from unittest.mock import MagicMock

from ai.claude_client import AIServiceError
from ai.conversation import ConversationManager
from app.orchestrator import Assistant
from app.state import AssistantState, StateManager
from security.confirmation import SecurityGuard
from tools.base import Tool, ToolRegistry, ToolResult


def text_block(text: str) -> SimpleNamespace:
    return SimpleNamespace(type="text", text=text)


def tool_use_block(tool_id: str, name: str, arguments: dict) -> SimpleNamespace:
    return SimpleNamespace(type="tool_use", id=tool_id, name=name, input=arguments)


def response(*blocks: SimpleNamespace) -> SimpleNamespace:
    return SimpleNamespace(content=list(blocks))


class FakeDangerousTool(Tool):
    name = "close_application"
    description = "Beendet eine Anwendung."
    parameters = {"type": "object", "properties": {}, "required": []}
    dangerous = True

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def confirmation_message(self, arguments: dict) -> str:
        return f"Soll ich '{arguments.get('application')}' wirklich beenden?"

    def execute(self, arguments: dict) -> ToolResult:
        self.calls.append(arguments)
        return ToolResult(success=True, message=f"{arguments.get('application')} wurde beendet.")


def make_assistant(claude_client, tool_registry: ToolRegistry | None = None) -> tuple[Assistant, StateManager]:
    registry = tool_registry or ToolRegistry()
    state_manager = StateManager()
    assistant = Assistant(
        claude_client=claude_client,
        tool_registry=registry,
        conversation=ConversationManager(),
        security_guard=SecurityGuard(),
        state_manager=state_manager,
    )
    return assistant, state_manager


def test_simple_text_reply() -> None:
    claude = MagicMock()
    claude.send.return_value = response(text_block("Natuerlich, wie kann ich helfen?"))
    assistant, state_manager = make_assistant(claude)

    reply = assistant.handle_text("Hallo Jarvis")

    assert reply == "Natuerlich, wie kann ich helfen?"
    assert state_manager.state == AssistantState.IDLE


def test_safe_tool_call_executes_directly() -> None:
    class EchoTool(Tool):
        name = "calculator"
        description = "x"
        parameters = {"type": "object", "properties": {}, "required": []}

        def execute(self, arguments: dict) -> ToolResult:
            return ToolResult(success=True, message="Das Ergebnis ist 9.065.")

    registry = ToolRegistry()
    registry.register(EchoTool())

    claude = MagicMock()
    claude.send.side_effect = [
        response(tool_use_block("1", "calculator", {"expression": "245*37"})),
        response(text_block("Das Ergebnis ist 9.065.")),
    ]
    assistant, _ = make_assistant(claude, registry)

    reply = assistant.handle_text("Was ist 245 mal 37?")

    assert reply == "Das Ergebnis ist 9.065."
    assert claude.send.call_count == 2


def test_dangerous_tool_call_requires_confirmation_before_executing() -> None:
    dangerous_tool = FakeDangerousTool()
    registry = ToolRegistry()
    registry.register(dangerous_tool)

    claude = MagicMock()
    claude.send.side_effect = [
        response(tool_use_block("1", "close_application", {"application": "notepad"})),
        response(text_block("Soll ich 'notepad' wirklich beenden?")),
    ]
    assistant, _ = make_assistant(claude, registry)

    reply = assistant.handle_text("Schliesse Notepad")

    assert "wirklich" in reply.lower()
    assert dangerous_tool.calls == []
    assert assistant.pending_action is not None
    assert assistant.pending_action.tool_name == "close_application"


def test_confirming_pending_action_executes_tool() -> None:
    dangerous_tool = FakeDangerousTool()
    registry = ToolRegistry()
    registry.register(dangerous_tool)

    claude = MagicMock()
    claude.send.side_effect = [
        response(tool_use_block("1", "close_application", {"application": "notepad"})),
        response(text_block("Soll ich 'notepad' wirklich beenden?")),
        response(text_block("Notepad wurde beendet.")),
    ]
    assistant, state_manager = make_assistant(claude, registry)

    assistant.handle_text("Schliesse Notepad")
    reply = assistant.handle_text("Ja")

    assert dangerous_tool.calls == [{"application": "notepad"}]
    assert assistant.pending_action is None
    assert reply == "Notepad wurde beendet."
    assert state_manager.state == AssistantState.IDLE


def test_declining_pending_action_cancels_without_executing() -> None:
    dangerous_tool = FakeDangerousTool()
    registry = ToolRegistry()
    registry.register(dangerous_tool)

    claude = MagicMock()
    claude.send.side_effect = [
        response(tool_use_block("1", "close_application", {"application": "notepad"})),
        response(text_block("Soll ich 'notepad' wirklich beenden?")),
    ]
    assistant, _ = make_assistant(claude, registry)

    assistant.handle_text("Schliesse Notepad")
    reply = assistant.handle_text("Nein")

    assert dangerous_tool.calls == []
    assert assistant.pending_action is None
    assert "abgebrochen" in reply.lower()
    # Claude wurde fuer die Ablehnung nicht erneut aufgerufen.
    assert claude.send.call_count == 2


def test_ai_service_error_is_surfaced_and_sets_error_state() -> None:
    claude = MagicMock()
    claude.send.side_effect = AIServiceError("Ich kann den KI-Dienst momentan nicht erreichen.")
    assistant, state_manager = make_assistant(claude)

    reply = assistant.handle_text("Hallo")

    assert reply == "Ich kann den KI-Dienst momentan nicht erreichen."
    assert state_manager.state == AssistantState.ERROR


def test_unexpected_exception_is_handled_gracefully() -> None:
    claude = MagicMock()
    claude.send.side_effect = RuntimeError("etwas ganz Unerwartetes")
    assistant, state_manager = make_assistant(claude)

    reply = assistant.handle_text("Hallo")

    assert reply == "Es ist ein unerwarteter Fehler aufgetreten."
    assert state_manager.state == AssistantState.ERROR
