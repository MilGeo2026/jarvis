"""Minimalistische JARVIS-Oberflaeche (PySide6)."""
from __future__ import annotations

import logging

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.orchestrator import Assistant
from app.state import StateManager
from ui.styles import STATE_COLORS, STYLESHEET
from voice.pipeline import VoiceComponents, VoicePipeline

logger = logging.getLogger("jarvis.ui")


class _AssistantWorker(QThread):
    finished_with_reply = Signal(str)

    def __init__(self, assistant: Assistant, text: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._assistant = assistant
        self._text = text

    def run(self) -> None:
        reply = self._assistant.handle_text(self._text)
        self.finished_with_reply.emit(reply)


class _VoiceWorker(QThread):
    def __init__(self, pipeline: VoicePipeline, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pipeline = pipeline

    def run(self) -> None:
        self._pipeline.run_forever()

    def request_stop(self) -> None:
        self._pipeline.stop()


class MainWindow(QWidget):
    state_changed = Signal(str)
    user_text_received = Signal(str)
    assistant_replied = Signal(str)

    def __init__(
        self,
        assistant: Assistant,
        state_manager: StateManager,
        voice_components: VoiceComponents | None = None,
    ) -> None:
        super().__init__()
        self._assistant = assistant
        self._state_manager = state_manager
        self._voice_components = voice_components
        self._voice_pipeline: VoicePipeline | None = None
        self._voice_worker: _VoiceWorker | None = None
        self._assistant_worker: _AssistantWorker | None = None

        self.setWindowTitle("JARVIS")
        self.resize(480, 640)
        self.setStyleSheet(STYLESHEET)

        self._build_ui()

        self.state_changed.connect(self._on_state_changed)
        self.user_text_received.connect(lambda text: self._append_transcript("Du", text))
        self.assistant_replied.connect(lambda text: self._append_transcript("JARVIS", text))
        self._state_manager.subscribe(lambda state: self.state_changed.emit(state.value))

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        title = QLabel("JARVIS")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        state_row = QHBoxLayout()
        self._state_dot = QLabel("◉")
        self._state_label = QLabel("IDLE")
        self._state_label.setObjectName("stateLabel")
        state_row.addStretch()
        state_row.addWidget(self._state_dot)
        state_row.addWidget(self._state_label)
        state_row.addStretch()
        layout.addLayout(state_row)
        self._apply_state_color("IDLE")

        self._transcript = QTextEdit()
        self._transcript.setObjectName("transcript")
        self._transcript.setReadOnly(True)
        layout.addWidget(self._transcript, 1)

        input_row = QHBoxLayout()
        self._input = QLineEdit()
        self._input.setPlaceholderText("Nachricht an JARVIS ...")
        self._input.returnPressed.connect(self._on_send_clicked)
        send_button = QPushButton("Senden")
        send_button.clicked.connect(self._on_send_clicked)
        input_row.addWidget(self._input)
        input_row.addWidget(send_button)
        layout.addLayout(input_row)

        footer_row = QHBoxLayout()
        self._mic_button = QPushButton("\U0001F399 Mikrofon")
        self._mic_button.setCheckable(True)
        self._mic_button.setEnabled(self._voice_components is not None)
        self._mic_button.clicked.connect(self._on_mic_toggled)
        self._voice_label = QLabel("\U0001F50A Stimme")
        footer_row.addWidget(self._mic_button)
        footer_row.addStretch()
        footer_row.addWidget(self._voice_label)
        layout.addLayout(footer_row)

    def _append_transcript(self, speaker: str, text: str) -> None:
        self._transcript.append(f"<b>{speaker}:</b> {text}")

    def _on_send_clicked(self) -> None:
        text = self._input.text().strip()
        if not text:
            return
        self._input.clear()
        self._append_transcript("Du", text)
        self._assistant_worker = _AssistantWorker(self._assistant, text, self)
        self._assistant_worker.finished_with_reply.connect(self._on_assistant_reply)
        self._assistant_worker.start()

    def _on_assistant_reply(self, reply: str) -> None:
        self._append_transcript("JARVIS", reply)

    def _handle_voice_text(self, text: str) -> str:
        """Wird aus dem Voice-Worker-Thread aufgerufen; Signale sorgen fuer thread-sicheres UI-Update."""
        self.user_text_received.emit(text)
        reply = self._assistant.handle_text(text)
        self.assistant_replied.emit(reply)
        return reply

    def _on_mic_toggled(self, checked: bool) -> None:
        if self._voice_components is None:
            return
        if checked:
            self._voice_pipeline = VoicePipeline(
                microphone=self._voice_components.microphone,
                stt=self._voice_components.stt,
                tts=self._voice_components.tts,
                wake_word=self._voice_components.wake_word,
                state_manager=self._state_manager,
                on_user_text=self._handle_voice_text,
            )
            self._voice_worker = _VoiceWorker(self._voice_pipeline, self)
            self._voice_worker.start()
        elif self._voice_worker is not None:
            self._voice_worker.request_stop()

    def _apply_state_color(self, state_value: str) -> None:
        color = STATE_COLORS.get(state_value, "#888888")
        self._state_dot.setStyleSheet(f"color: {color}; font-size: 20px;")

    def _on_state_changed(self, state_value: str) -> None:
        self._state_label.setText(state_value)
        self._apply_state_color(state_value)


def run_gui(
    assistant: Assistant,
    state_manager: StateManager,
    voice_components: VoiceComponents | None = None,
) -> int:
    app = QApplication.instance() or QApplication([])
    window = MainWindow(assistant, state_manager, voice_components)
    window.show()
    return app.exec()
