import threading
import time
from unittest.mock import MagicMock

import pytest

import ui.sound as sound_module
from ui.sound import SoundPlayer


def _run_synchronously(monkeypatch: pytest.MonkeyPatch) -> None:
    """Laesst den Sound-Thread synchron laufen, damit Tests nicht auf Threads warten muessen."""

    class ImmediateThread:
        def __init__(self, target, daemon=None):
            self._target = target

        def start(self):
            self._target()

    monkeypatch.setattr(threading, "Thread", ImmediateThread)


def test_sound_disabled_does_not_beep(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_winsound = MagicMock()
    monkeypatch.setattr(sound_module, "winsound", fake_winsound)
    _run_synchronously(monkeypatch)

    player = SoundPlayer(enabled=False)
    player.play_online()
    player.play_wake()
    player.play_confirm()

    fake_winsound.Beep.assert_not_called()


def test_sound_enabled_plays_beep(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_winsound = MagicMock()
    monkeypatch.setattr(sound_module, "winsound", fake_winsound)
    _run_synchronously(monkeypatch)

    player = SoundPlayer(enabled=True)
    player.play_wake()

    fake_winsound.Beep.assert_called()


def test_sound_missing_winsound_is_noop(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sound_module, "winsound", None)
    _run_synchronously(monkeypatch)

    player = SoundPlayer(enabled=True)
    # Darf nicht werfen, auch ohne winsound (z. B. auf Nicht-Windows-Systemen).
    player.play_online()


def test_sound_beep_failure_is_caught(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_winsound = MagicMock()
    fake_winsound.Beep.side_effect = RuntimeError("kein Audiogeraet")
    monkeypatch.setattr(sound_module, "winsound", fake_winsound)
    _run_synchronously(monkeypatch)

    player = SoundPlayer(enabled=True)
    player.play_confirm()  # darf nicht werfen
