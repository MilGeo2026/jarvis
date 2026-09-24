"""Verbindet Mikrofon, Wake Word, STT, KI-Antwort und TTS zu einer Pipeline."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable

from app.state import AssistantState, StateManager
from voice.microphone import Microphone, MicrophoneError, RecordingTooShortError
from voice.speech_to_text import SpeechToText, SpeechToTextError
from voice.text_to_speech import TextToSpeech, TextToSpeechError
from voice.wake_word import WakeWordDetector

logger = logging.getLogger("jarvis.voice")

OnUserText = Callable[[str], str]


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
    ) -> None:
        self._microphone = microphone
        self._stt = stt
        self._tts = tts
        self._wake_word = wake_word
        self._state = state_manager
        self._on_user_text = on_user_text
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
            self.listen_and_respond_once()
            if not self._wake_word.enabled:
                break

    def listen_and_respond_once(self) -> str | None:
        """Nimmt eine einzelne Nutzeraeusserung auf, verarbeitet sie und spricht die Antwort."""
        self._state.set(AssistantState.LISTENING)
        logger.info("Zuhoeren")
        try:
            audio = self._microphone.record_utterance()
            text = self._stt.transcribe(audio, self._microphone.sample_rate)
        except MicrophoneError as exc:
            self._state.set(AssistantState.ERROR)
            self._speak_safely(str(exc))
            return None
        except RecordingTooShortError:
            self._state.set(AssistantState.IDLE)
            return None
        except SpeechToTextError as exc:
            self._state.set(AssistantState.ERROR)
            self._speak_safely(str(exc))
            return None

        logger.info("Benutzer: %s", text)
        self._state.set(AssistantState.THINKING)
        reply = self._on_user_text(text)

        self._state.set(AssistantState.SPEAKING)
        logger.info("Antwort wird vorgelesen")
        self._speak_safely(reply)
        self._state.set(AssistantState.IDLE)
        return reply

    def _speak_safely(self, text: str) -> None:
        try:
            self._tts.speak(text)
        except TextToSpeechError:
            logger.warning("Sprachausgabe fehlgeschlagen, Antwort bleibt nur als Text sichtbar.")
