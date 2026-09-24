from unittest.mock import MagicMock

import pytest

import ui.hotkey as hotkey_module
from ui.hotkey import GlobalHotkey


def test_start_returns_false_when_pynput_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(hotkey_module, "keyboard", None)
    hk = GlobalHotkey("<ctrl>+<space>")
    assert hk.start() is False


def test_start_registers_listener_with_correct_combo(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_listener = MagicMock()
    fake_keyboard = MagicMock()
    fake_keyboard.GlobalHotKeys.return_value = fake_listener
    monkeypatch.setattr(hotkey_module, "keyboard", fake_keyboard)

    hk = GlobalHotkey("<ctrl>+<space>")
    assert hk.start() is True

    args, _ = fake_keyboard.GlobalHotKeys.call_args
    combo_map = args[0]
    assert "<ctrl>+<space>" in combo_map
    fake_listener.start.assert_called_once()


def test_activated_signal_fires_on_callback(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_listener = MagicMock()
    fake_keyboard = MagicMock()
    fake_keyboard.GlobalHotKeys.return_value = fake_listener
    monkeypatch.setattr(hotkey_module, "keyboard", fake_keyboard)

    hk = GlobalHotkey("<ctrl>+<space>")
    received = []
    hk.activated.connect(lambda: received.append(True))
    hk.start()

    args, _ = fake_keyboard.GlobalHotKeys.call_args
    callback = args[0]["<ctrl>+<space>"]
    callback()

    assert received == [True]


def test_stop_stops_listener(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_listener = MagicMock()
    fake_keyboard = MagicMock()
    fake_keyboard.GlobalHotKeys.return_value = fake_listener
    monkeypatch.setattr(hotkey_module, "keyboard", fake_keyboard)

    hk = GlobalHotkey("<ctrl>+<space>")
    hk.start()
    hk.stop()

    fake_listener.stop.assert_called_once()


def test_start_handles_registration_failure_gracefully(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_keyboard = MagicMock()
    fake_keyboard.GlobalHotKeys.side_effect = RuntimeError("boom")
    monkeypatch.setattr(hotkey_module, "keyboard", fake_keyboard)

    hk = GlobalHotkey("<ctrl>+<space>")
    assert hk.start() is False
