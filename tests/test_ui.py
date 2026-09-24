"""Rauchtest fuer die GUI. Laeuft "offscreen", falls in der Umgebung kein Display verfuegbar ist."""
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

from app.state import AssistantState, StateManager  # noqa: E402
from ui.main_window import MainWindow  # noqa: E402


def test_main_window_reflects_state_changes() -> None:
    assistant = MagicMock()
    state_manager = StateManager()
    window = MainWindow(assistant, state_manager, voice_components=None)

    state_manager.set(AssistantState.LISTENING)

    assert window._state_label.text() == "LISTENING"
    assert window._mic_button.isEnabled() is False


def test_main_window_sends_text_message() -> None:
    assistant = MagicMock()
    assistant.handle_text.return_value = "Natuerlich."
    state_manager = StateManager()
    window = MainWindow(assistant, state_manager, voice_components=None)

    window._input.setText("Wie spaet ist es?")
    window._on_send_clicked()
    if window._assistant_worker is not None:
        window._assistant_worker.wait(2000)

    assert "Wie spaet ist es?" in window._transcript.toPlainText()
