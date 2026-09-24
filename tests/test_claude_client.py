from unittest.mock import MagicMock, patch

import anthropic
import pytest

from ai.claude_client import AIServiceError, ClaudeClient, extract_text, to_plain_content
from app.config import Settings
from tools import build_default_registry


def _make_client(settings: Settings) -> ClaudeClient:
    return ClaudeClient(settings, build_default_registry())


def test_send_without_api_key_raises_ai_service_error(base_env, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    settings = Settings.load(env_file=None)
    client = _make_client(settings)
    with pytest.raises(AIServiceError):
        client.send([{"role": "user", "content": "hallo"}])


def test_send_success_returns_response(settings: Settings) -> None:
    client = _make_client(settings)
    fake_response = MagicMock()
    with patch("anthropic.Anthropic") as mock_anthropic_cls:
        mock_anthropic_cls.return_value.messages.create.return_value = fake_response
        response = client.send([{"role": "user", "content": "hallo"}])
    assert response is fake_response


def test_send_connection_error_becomes_ai_service_error(settings: Settings) -> None:
    client = _make_client(settings)
    with patch("anthropic.Anthropic") as mock_anthropic_cls:
        mock_anthropic_cls.return_value.messages.create.side_effect = anthropic.APIConnectionError(
            request=MagicMock()
        )
        with pytest.raises(AIServiceError, match="nicht erreichen"):
            client.send([{"role": "user", "content": "hallo"}])


def test_extract_text_joins_text_blocks() -> None:
    block1 = MagicMock(type="text", text="Hallo")
    block2 = MagicMock(type="tool_use")
    block3 = MagicMock(type="text", text="Welt")
    assert extract_text([block1, block2, block3]) == "Hallo Welt"


def test_to_plain_content_converts_tool_use() -> None:
    block = MagicMock(type="tool_use", id="1", input={"expression": "1+1"})
    block.name = "calculator"  # "name" ist ein reserviertes MagicMock-Kwarg, daher separat gesetzt
    plain = to_plain_content([block])
    assert plain == [{"type": "tool_use", "id": "1", "name": "calculator", "input": {"expression": "1+1"}}]
