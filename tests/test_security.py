from security.confirmation import PendingAction, SecurityGuard, interpret_yes_no
from tools.application_tools import CloseApplicationTool, OpenWebsiteTool


def test_interpret_yes_no_affirmative() -> None:
    assert interpret_yes_no("Ja") is True
    assert interpret_yes_no("ja, mach das") is True
    assert interpret_yes_no("Klar!") is True


def test_interpret_yes_no_negative() -> None:
    assert interpret_yes_no("Nein") is False
    assert interpret_yes_no("nein, lass es") is False
    assert interpret_yes_no("Stopp") is False


def test_interpret_yes_no_ambiguous() -> None:
    assert interpret_yes_no("Wie ist das Wetter?") is None
    assert interpret_yes_no("") is None


def test_security_guard_flags_dangerous_tool() -> None:
    guard = SecurityGuard()
    tool = CloseApplicationTool()
    dangerous, question = guard.evaluate(tool, {"application": "notepad"})
    assert dangerous is True
    assert "notepad" in question


def test_security_guard_allows_safe_tool() -> None:
    guard = SecurityGuard()
    tool = OpenWebsiteTool()
    dangerous, question = guard.evaluate(tool, {"url": "https://example.com"})
    assert dangerous is False
    assert question == ""


def test_pending_action_dataclass() -> None:
    action = PendingAction(tool_name="close_application", arguments={"application": "notepad"}, question="Sicher?")
    assert action.tool_name == "close_application"
    assert action.arguments["application"] == "notepad"
