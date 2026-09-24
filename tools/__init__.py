"""Tool-Paket: stellt die Standard-Tool-Registry von JARVIS bereit."""
from tools.application_tools import CloseApplicationTool, OpenApplicationTool, OpenWebsiteTool
from tools.base import Tool, ToolRegistry, ToolResult
from tools.calculator_tools import CalculatorTool
from tools.communication_tools import SendNotificationTool
from tools.file_tools import CopyFileTool, CreateFileTool, MoveFileTool, ReadFileTool, SearchFilesTool
from tools.system_tools import GetCurrentDateTool, GetCurrentTimeTool, GetSystemInformationTool
from tools.web_tools import WebSearchTool

__all__ = ["Tool", "ToolResult", "ToolRegistry", "build_default_registry"]


def build_default_registry() -> ToolRegistry:
    """Erstellt eine ToolRegistry mit allen eingebauten Tools.

    Neue Tools koennen hinzugefuegt werden, indem eine Tool-Unterklasse
    geschrieben und hier zusaetzlich registriert wird.
    """
    registry = ToolRegistry()
    for tool_cls in (
        GetSystemInformationTool,
        GetCurrentTimeTool,
        GetCurrentDateTool,
        OpenApplicationTool,
        CloseApplicationTool,
        OpenWebsiteTool,
        SearchFilesTool,
        ReadFileTool,
        CreateFileTool,
        MoveFileTool,
        CopyFileTool,
        WebSearchTool,
        SendNotificationTool,
        CalculatorTool,
    ):
        registry.register(tool_cls())
    return registry
