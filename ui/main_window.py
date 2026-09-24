"""JARVIS-HUD-Fenster: hostet die QML-Oberflaeche und verbindet sie mit dem Assistenten."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QEvent, QObject, QPoint, Qt, QThread, QTimer, QUrl, Signal
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtWidgets import QVBoxLayout, QWidget

from app.events import ActivityBus, AudioLevelBus
from app.orchestrator import Assistant
from app.state import AssistantState, StateManager
from ui.bridge import JarvisBridge
from ui.sound import SoundPlayer
from ui.window_controller import WindowMode, apply_window_mode, requires_manual_drag
from voice.pipeline import VoiceComponents, VoicePipeline

logger = logging.getLogger("jarvis.ui")

QML_MAIN = Path(__file__).parent / "qml" / "Main.qml"

# Dauer der Boot-Sequenz in ms, abgestimmt auf die Choreographie in BootSequence.qml.
BOOT_SEQUENCE_DURATION_MS = 2200
ERROR_DISPLAY_DURATION_MS = 1500


class _AssistantWorker(QThread):
    finished_with_reply = Signal(str)

    def __init__(self, assistant: Assistant, text: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._assistant = assistant
        self._text = text

    def run(self) -> None:
        reply = self._assistant.handle_text(self._text)
        self.finished_with_reply.emit(reply)


class _VoiceWorker(QThread):
    def __init__(self, pipeline: VoicePipeline, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._pipeline = pipeline

    def run(self) -> None:
        self._pipeline.run_forever()

    def request_stop(self) -> None:
        self._pipeline.stop()


class JarvisWindow(QWidget):
    """Frameloses/normale HUD-Fenster. Die eigentliche Darstellung lebt komplett in QML."""

    def __init__(
        self,
        assistant: Assistant,
        bridge: JarvisBridge,
        state_manager: StateManager,
        activity_bus: ActivityBus,
        audio_level_bus: AudioLevelBus,
        sound: SoundPlayer,
        window_mode: WindowMode,
        always_on_top: bool = False,
        voice_components: Optional[VoiceComponents] = None,
        wake_word_enabled: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._assistant = assistant
        self._bridge = bridge
        self._state_manager = state_manager
        self._activity_bus = activity_bus
        self._audio_level_bus = audio_level_bus
        self._sound = sound
        self._window_mode = window_mode
        self._voice_components = voice_components
        self._wake_word_enabled = wake_word_enabled
        self._voice_pipeline: VoicePipeline | None = None
        self._voice_worker: _VoiceWorker | None = None
        self._assistant_worker: _AssistantWorker | None = None
        self._drag_position: QPoint | None = None

        self.setWindowTitle("JARVIS")
        self.resize(1024, 768)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._quick_widget = QQuickWidget()
        self._quick_widget.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
        self._quick_widget.setClearColor(Qt.GlobalColor.transparent)
        self._quick_widget.rootContext().setContextProperty("bridge", bridge)
        self._quick_widget.setSource(QUrl.fromLocalFile(str(QML_MAIN)))
        for error in self._quick_widget.errors():
            logger.error("QML-Fehler: %s", error.toString())
        self._quick_widget.installEventFilter(self)
        layout.addWidget(self._quick_widget)

        bridge.textSubmitted.connect(self._on_text_submitted)
        state_manager.subscribe(self._on_state_changed_for_sound)

        apply_window_mode(self, window_mode, always_on_top)
        self._start_voice_loop_if_enabled()

    # -- Text-Eingabe (sekundaerer Kanal) --

    def _on_text_submitted(self, text: str) -> None:
        self._assistant_worker = _AssistantWorker(self._assistant, text, self)
        self._assistant_worker.finished_with_reply.connect(self._on_assistant_reply)
        self._assistant_worker.start()

    def _on_assistant_reply(self, reply: str) -> None:
        self._activity_bus.publish(reply)
        if self._state_manager.state == AssistantState.ERROR:
            QTimer.singleShot(ERROR_DISPLAY_DURATION_MS, lambda: self._state_manager.set(AssistantState.STANDBY))
        else:
            self._state_manager.set(AssistantState.STANDBY)

    # -- Sprachschleife (primaerer Kanal) --

    def _start_voice_loop_if_enabled(self) -> None:
        if self._voice_components is None or not self._wake_word_enabled:
            return
        self._voice_pipeline = VoicePipeline(
            microphone=self._voice_components.microphone,
            stt=self._voice_components.stt,
            tts=self._voice_components.tts,
            wake_word=self._voice_components.wake_word,
            state_manager=self._state_manager,
            on_user_text=self._assistant.handle_text,
            activity_bus=self._activity_bus,
            audio_level_bus=self._audio_level_bus,
            on_wake_detected=self._sound.play_wake,
        )
        self._voice_worker = _VoiceWorker(self._voice_pipeline, self)
        self._voice_worker.start()

    def _on_state_changed_for_sound(self, state: AssistantState) -> None:
        if state == AssistantState.EXECUTING:
            self._sound.play_confirm()

    # -- Boot-Sequenz --

    def finish_boot_sequence(self, delay_ms: int = BOOT_SEQUENCE_DURATION_MS) -> None:
        QTimer.singleShot(delay_ms, self._complete_boot)

    def _complete_boot(self) -> None:
        self._bridge.hide_boot()
        self._sound.play_online()

    # -- Fenster-Drag im rahmenlosen Modus --

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched is self._quick_widget and requires_manual_drag(self._window_mode):
            if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            elif event.type() == QEvent.Type.MouseMove and self._drag_position is not None:
                if event.buttons() & Qt.MouseButton.LeftButton:
                    self.move(event.globalPosition().toPoint() - self._drag_position)
            elif event.type() == QEvent.Type.MouseButtonRelease:
                self._drag_position = None
        return super().eventFilter(watched, event)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape and self.isFullScreen():
            self.showNormal()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event) -> None:
        if self._voice_worker is not None:
            if self._voice_pipeline is not None:
                self._voice_pipeline.stop()
            self._voice_worker.wait(2000)
        super().closeEvent(event)

    def toggle_visibility(self) -> None:
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()
