"""Verbindet Mikrofon, Wake Word, STT, KI-Antwort und TTS zu einer Pipeline."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Optional

from app.events import ActivityBus, AudioLevelBus
from app.state import AssistantState, StateManager
from voice.microphone import Microphone, MicrophoneError, RecordingTooShortError
from voice.speech_to_text import SpeechToText, SpeechToTextError
from voice.text_to_speech import TextToSpeech, TextToSpeechError
from voice.wake_word import WakeWordDetector

logger = logging.getLogger("jarvis.voice")

OnUserText = Callable[[str], str]
OnWakeDetected = Callable[[], None]


@dataclass
class VoiceComponents:
    """Buendelt die konkreten Voice-Implementierungen fuer die Pipeline-Erstellung (z. B. durch die GUI)."""

    microphone: Microphone
    stt: SpeechToText
    tts: TextToSpeech
    wake_word: WakeWordDetector


class VoicePipeline:
    """Mikrofon -> (Wake Word) -> Speech-to-Text -> KI -> Text-to-Speech -> Lautsprecher."""

    def __init__(
        self,
        microphone: Microphone,
        stt: SpeechToText,
        tts: TextToSpeech,
        wake_word: WakeWordDetector,
        state_manager: StateManager,
        on_user_text: OnUserText,
        activity_bus: Optional[ActivityBus] = None,
        audio_level_bus: Optional[AudioLevelBus] = None,
        on_wake_detected: Optional[OnWakeDetected] = None,
    ) -> None:
        self._microphone = microphone
        self._stt = stt
        self._tts = tts
        self._wake_word = wake_word
        self._state = state_manager
        self._on_user_text = on_user_text
        self._activity = activity_bus or ActivityBus()
        self._audio_level = audio_level_bus or AudioLevelBus()
        self._on_wake_detected = on_wake_detected
        self._running = False

    def stop(self) -> None:
        self._running = False

    def run_forever(self) -> None:
        """Laeuft dauerhaft: wartet auf das Wake Word (falls aktiv) und verarbeitet dann eine Aeusserung."""
        self._running = True
        while self._running:
            if self._wake_word.enabled:
                logger.info("Warte auf Aktivierungswort")
                if not self._wake_word.listen_once():
                    continue
                logger.info("Aktivierungswort erkannt")
                if self._on_wake_detected is not None:
                    self._on_wake_detected()
            self.listen_and_respond_once()
            if not self._wake_word.enabled:
                break

    def listen_and_respond_once(self) -> str | None:
        """Nimmt eine einzelne Nutzeraeusserung auf, verarbeitet sie und spricht die Antwort."""
        self._state.set(AssistantState.LISTENING)
        self._activity.publish("")
        logger.info("Zuhoeren")
        try:
            audio = self._microphone.record_utterance(on_level=self._audio_level.publish)
            text = self._stt.transcribe(audio, self._microphone.sample_rate)
        except MicrophoneError as exc:
            self._state.set(AssistantState.ERROR)
            self._activity.publish(str(exc))
            self._speak_safely(str(exc))
            self._state.set(AssistantState.STANDBY)
            return None
        except RecordingTooShortError:
            self._state.set(AssistantState.STANDBY)
            return None
        except SpeechToTextError as exc:
            self._state.set(AssistantState.ERROR)
            self._activity.publish(str(exc))
            self._speak_safely(str(exc))
            self._state.set(AssistantState.STANDBY)
            return None
        finally:
            self._audio_level.publish(0.0)

        logger.info("Benutzer: %s", text)
        self._activity.publish(text)
        self._state.set(AssistantState.THINKING)
        reply = self._on_user_text(text)

        if self._state.state != AssistantState.ERROR:
            self._state.set(AssistantState.SPEAKING)
        self._activity.publish(reply)
        logger.info("Antwort wird vorgelesen")
        self._speak_safely(reply)
        self._state.set(AssistantState.STANDBY)
        return reply

    def _speak_safely(self, text: str) -> None:
        try:
            self._tts.speak(text)
        except TextToSpeechError:
            logger.warning("Sprachausgabe fehlgeschlagen, Antwort bleibt nur als Text sichtbar.")
