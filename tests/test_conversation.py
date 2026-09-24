import pytest

from ai.conversation import ConversationManager


def test_add_user_and_assistant() -> None:
    conv = ConversationManager()
    conv.add_user("Hallo")
    conv.add_assistant("Hi, wie kann ich helfen?")
    messages = conv.get_messages()
    assert messages == [
        {"role": "user", "content": "Hallo"},
        {"role": "assistant", "content": "Hi, wie kann ich helfen?"},
    ]


def test_add_raw_preserves_tool_blocks() -> None:
    conv = ConversationManager()
    conv.add_user("Öffne Spotify")
    conv.add_raw({"role": "assistant", "content": [{"type": "tool_use", "id": "1", "name": "open_application", "input": {}}]})
    conv.add_raw({"role": "user", "content": [{"type": "tool_result", "tool_use_id": "1", "content": "ok"}]})
    conv.add_assistant("Spotify ist geoeffnet.")
    assert len(conv.get_messages()) == 4


def test_clear_resets_history() -> None:
    conv = ConversationManager()
    conv.add_user("Test")
    conv.clear()
    assert conv.get_messages() == []


def test_trim_keeps_history_within_limit_at_clean_boundaries() -> None:
    conv = ConversationManager(max_messages=4)
    for i in range(10):
        conv.add_user(f"Nachricht {i}")
        conv.add_assistant(f"Antwort {i}")
    messages = conv.get_messages()
    assert len(messages) <= 4
    # Historie muss an einer sauberen Nutzer-Text-Grenze beginnen.
    assert messages[0]["role"] == "user"
    assert isinstance(messages[0]["content"], str)


def test_trim_does_not_split_tool_exchange() -> None:
    conv = ConversationManager(max_messages=2)
    conv.add_user("Erste Anfrage")
    conv.add_raw({"role": "assistant", "content": [{"type": "tool_use", "id": "1", "name": "t", "input": {}}]})
    conv.add_raw({"role": "user", "content": [{"type": "tool_result", "tool_use_id": "1", "content": "ok"}]})
    conv.add_assistant("Fertig")
    conv.add_user("Zweite Anfrage")
    conv.add_assistant("Antwort zwei")

    messages = conv.get_messages()
    # Es darf kein verwaistes tool_result ohne zugehoerigen tool_use uebrig bleiben.
    for message in messages:
        content = message["content"]
        if isinstance(content, list):
            for block in content:
                if block.get("type") == "tool_result":
                    pytest.fail("tool_result ohne Kontext sollte durch Trimmen ganzer Austausche vermieden werden")
