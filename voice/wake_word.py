"""Wake-Word-Erkennung.

MVP-Implementierung: es wird kein zusaetzlicher (kostenpflichtiger) Wake-Word-
Dienst benoetigt. Stattdessen wird ein kurzes Audiofenster ueber die vorhandene
SpeechToText-Schnittstelle transkribiert und auf das Aktivierungswort geprueft.
Die Erkennung kann jederzeit ueber WAKE_WORD_ENABLED=false deaktiviert werden,
ohne den restlichen Code zu aendern (dann wird die manuelle Aktivierung genutzt).
"""
from __future__ import annotations

import logging

from voice.microphone import Microphone, MicrophoneError, RecordingTooShortError
from voice.speech_to_text import SpeechToText, SpeechToTextError

logger = logging.getLogger("jarvis.voice")


class WakeWordDetector:
    def __init__(self, wake_word: str, stt: SpeechToText, microphone: Microphone, enabled: bool = True) -> None:
        self.wake_word = wake_word.lower().strip()
        self._stt = stt
        self._microphone = microphone
        self.enabled = enabled

    def listen_once(self) -> bool:
        """Nimmt ein kurzes Audiofenster auf und prueft, ob das Aktivierungswort enthalten ist."""
        if not self.enabled:
            return False
        try:
            audio = self._microphone.record_utterance()
            text = self._stt.transcribe(audio, self._microphone.sample_rate)
        except (MicrophoneError, RecordingTooShortError, SpeechToTextError):
            return False
        return self.wake_word in text.lower()
