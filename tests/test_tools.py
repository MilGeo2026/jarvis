from unittest.mock import MagicMock, patch

import pytest

from tools import build_default_registry
from tools.application_tools import CloseApplicationTool
from tools.calculator_tools import CalculationError, CalculatorTool, safe_eval
from tools.file_tools import CopyFileTool, CreateFileTool, MoveFileTool, ReadFileTool, SearchFilesTool
from tools.system_tools import GetCurrentDateTool, GetCurrentTimeTool, GetSystemInformationTool
from tools.web_tools import WebSearchTool


def test_registry_contains_all_required_tools() -> None:
    registry = build_default_registry()
    names = {tool.name for tool in registry.all()}
    assert names == {
        "get_system_information",
        "get_current_time",
        "get_current_date",
        "open_application",
        "close_application",
        "open_website",
        "search_files",
        "read_file",
        "create_file",
        "move_file",
        "copy_file",
        "web_search",
        "send_notification",
        "calculator",
    }


def test_registry_execute_unknown_tool_returns_failure() -> None:
    registry = build_default_registry()
    result = registry.execute("does_not_exist", {})
    assert result.success is False


def test_registry_execute_catches_exceptions() -> None:
    registry = build_default_registry()
    broken_tool = MagicMock()
    broken_tool.name = "broken"
    broken_tool.execute.side_effect = RuntimeError("boom")
    registry.register(broken_tool)
    result = registry.execute("broken", {})
    assert result.success is False
    assert "nicht ausgefuehrt" in result.message


def test_get_current_time_format() -> None:
    result = GetCurrentTimeTool().execute({})
    assert result.success is True
    assert "Uhr" in result.message


def test_get_current_date_format() -> None:
    result = GetCurrentDateTool().execute({})
    assert result.success is True
    assert "," in result.message


def test_get_system_information() -> None:
    result = GetSystemInformationTool().execute({})
    assert result.success is True
    assert "betriebssystem" in result.message


def test_close_application_is_dangerous() -> None:
    tool = CloseApplicationTool()
    assert tool.is_dangerous({"application": "notepad"}) is True
    assert "beenden" in tool.confirmation_message({"application": "notepad"})


def test_calculator_basic() -> None:
    result = CalculatorTool().execute({"expression": "245 * 37"})
    assert result.success is True
    assert result.data["result"] == 9065


def test_calculator_rejects_dangerous_expressions() -> None:
    with pytest.raises(CalculationError):
        safe_eval("__import__('os').system('echo hi')")


def test_calculator_invalid_expression_returns_failure() -> None:
    result = CalculatorTool().execute({"expression": "1 + "})
    assert result.success is False


def test_create_file_is_dangerous_only_when_exists(tmp_path) -> None:
    tool = CreateFileTool()
    target = tmp_path / "notizen.txt"
    assert tool.is_dangerous({"path": str(target)}) is False
    target.write_text("bereits da")
    assert tool.is_dangerous({"path": str(target)}) is True


def test_create_file_execute(tmp_path) -> None:
    target = tmp_path / "notizen.txt"
    result = CreateFileTool().execute({"path": str(target), "content": "Hallo Welt"})
    assert result.success is True
    assert target.read_text() == "Hallo Welt"


def test_read_file_missing_returns_failure(tmp_path) -> None:
    result = ReadFileTool().execute({"path": str(tmp_path / "fehlt.txt")})
    assert result.success is False


def test_read_file_success(tmp_path) -> None:
    target = tmp_path / "a.txt"
    target.write_text("Inhalt")
    result = ReadFileTool().execute({"path": str(target)})
    assert result.success is True
    assert result.message == "Inhalt"


def test_move_file_dangerous_when_destination_exists(tmp_path) -> None:
    tool = MoveFileTool()
    dest = tmp_path / "dest.txt"
    dest.write_text("existiert")
    assert tool.is_dangerous({"source": "x", "destination": str(dest)}) is True


def test_move_file_execute(tmp_path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("data")
    dest = tmp_path / "dest.txt"
    result = MoveFileTool().execute({"source": str(source), "destination": str(dest)})
    assert result.success is True
    assert dest.exists()
    assert not source.exists()


def test_copy_file_execute(tmp_path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("data")
    dest = tmp_path / "dest.txt"
    result = CopyFileTool().execute({"source": str(source), "destination": str(dest)})
    assert result.success is True
    assert dest.exists()
    assert source.exists()


def test_search_files_finds_match(tmp_path) -> None:
    (tmp_path / "notizen.txt").write_text("x")
    (tmp_path / "andere.md").write_text("x")
    result = SearchFilesTool().execute({"query": "notizen", "directory": str(tmp_path)})
    assert result.success is True
    assert any("notizen.txt" in match for match in result.data["matches"])


def test_web_search_handles_network_error() -> None:
    import requests

    with patch("tools.web_tools.requests.get", side_effect=requests.ConnectionError("network down")):
        result = WebSearchTool().execute({"query": "python"})
        assert result.success is False
