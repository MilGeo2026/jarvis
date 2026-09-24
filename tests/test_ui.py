"""Rauchtests fuer das QML-HUD-Fenster. Laeuft "offscreen" ohne echtes Display."""
import os
from unittest.mock import MagicMock

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pyside6 = pytest.importorskip("PySide6")

try:
    from PySide6.QtWidgets import QApplication

    _app = QApplication.instance() or QApplication([])
except Exception:  # pragma: no cover - Umgebung ohne nutzbares Qt-Backend
    _app = None

pytestmark = pytest.mark.skipif(_app is None, reason="Kein nutzbares Qt-Backend in dieser Umgebung verfuegbar")

from app.events import ActivityBus, AudioLevelBus  # noqa: E402
from app.state import AssistantState, StateManager  # noqa: E402
from ui.bridge import JarvisBridge  # noqa: E402
from ui.main_window import JarvisWindow  # noqa: E402
from ui.sound import SoundPlayer  # noqa: E402
from ui.theme import Theme  # noqa: E402
from ui.window_controller import WindowMode  # noqa: E402


def make_window(assistant=None):
    assistant = assistant or MagicMock()
    state_manager = StateManager()
    activity_bus = ActivityBus()
    audio_level_bus = AudioLevelBus()
    bridge = JarvisBridge(Theme(), state_manager, activity_bus, audio_level_bus, boot_sequence_enabled=False)
    sound = SoundPlayer(enabled=False)
    window = JarvisWindow(
        assistant=assistant,
        bridge=bridge,
        state_manager=state_manager,
        activity_bus=activity_bus,
        audio_level_bus=audio_level_bus,
        sound=sound,
        window_mode=WindowMode.NORMAL,
        voice_components=None,
        wake_word_enabled=False,
    )
    return window, assistant, state_manager, activity_bus, bridge


def test_window_loads_qml_without_errors() -> None:
    window, *_ = make_window()
    assert window._quick_widget.errors() == []
    assert window.windowTitle() == "JARVIS"


def test_text_submission_calls_assistant_and_updates_activity() -> None:
    assistant = MagicMock()
    assistant.handle_text.return_value = "Natuerlich."
    window, assistant, state_manager, activity_bus, bridge = make_window(assistant)

    bridge.submitText("Wie spaet ist es?")
    if window._assistant_worker is not None:
        window._assistant_worker.wait(2000)
    QApplication.processEvents()

    assistant.handle_text.assert_called_once_with("Wie spaet ist es?")
    assert activity_bus.value == "Natuerlich."
    assert state_manager.state == AssistantState.STANDBY


def test_error_reply_keeps_error_state_immediately_after() -> None:
    assistant = MagicMock()

    def fake_handle_text(text: str) -> str:
        state_manager.set(AssistantState.ERROR)
        return "Ich kann den KI-Dienst momentan nicht erreichen."

    assistant.handle_text.side_effect = fake_handle_text
    window, assistant, state_manager, activity_bus, bridge = make_window(assistant)

    bridge.submitText("Hallo")
    if window._assistant_worker is not None:
        window._assistant_worker.wait(2000)
    QApplication.processEvents()

    # Direkt nach der Antwort bleibt der Fehlerzustand kurz sichtbar (verzoegerter Reset).
    assert state_manager.state == AssistantState.ERROR


def test_executing_state_triggers_confirm_sound() -> None:
    window, assistant, state_manager, activity_bus, bridge = make_window()
    window._sound.enabled = True
    window._sound.play_confirm = MagicMock()

    state_manager.set(AssistantState.EXECUTING)

    window._sound.play_confirm.assert_called_once()


def test_finish_boot_sequence_hides_boot_and_plays_sound() -> None:
    window, *_ = make_window()
    window._sound.play_online = MagicMock()

    window.finish_boot_sequence(delay_ms=10)
    QApplication.processEvents()
    import time

    time.sleep(0.05)
    QApplication.processEvents()

    assert window._bridge.showBoot is False
    window._sound.play_online.assert_called_once()
