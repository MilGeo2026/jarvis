"""Austauschbare Text-to-Speech-Schnittstelle."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from app.config import Settings

logger = logging.getLogger("jarvis.voice")


class TextToSpeechError(Exception):
    pass


class TextToSpeech(ABC):
    @abstractmethod
    def speak(self, text: str) -> None: ...


class WindowsTTS(TextToSpeech):
    """Lokale Sprachausgabe ueber SAPI (Windows) via pyttsx3, kostenlos und offline."""

    def __init__(self, voice: str = "", speed: float = 1.0) -> None:
        self._voice = voice
        self._speed = speed
        self._engine: Any = None

    def _ensure_engine(self) -> Any:
        if self._engine is None:
            try:
                import pyttsx3
            except ImportError as exc:
                raise TextToSpeechError("Die Sprachausgabe ist nicht installiert.") from exc
            try:
                self._engine = pyttsx3.init()
            except Exception as exc:
                raise TextToSpeechError("Die Sprachausgabe konnte nicht gestartet werden.") from exc

            base_rate = self._engine.getProperty("rate")
            self._engine.setProperty("rate", int(base_rate * self._speed))
            if self._voice:
                for voice in self._engine.getProperty("voices"):
                    if self._voice.lower() in voice.name.lower() or self._voice == voice.id:
                        self._engine.setProperty("voice", voice.id)
                        break
        return self._engine

    def speak(self, text: str) -> None:
        if not text.strip():
            return
        engine = self._ensure_engine()
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception as exc:
            raise TextToSpeechError("Die Antwort konnte nicht vorgelesen werden.") from exc


class CloudTTS(TextToSpeech):
    """Platzhalter fuer einen hochwertigeren Cloud-TTS-Dienst (z. B. fuer eine natuerlichere Stimme).

    Erwartet einen API-Schluessel via Konfiguration; die konkrete Anbindung kann
    spaeter ergaenzt werden, ohne den Rest der Anwendung zu aendern.
    """

    def __init__(self, api_key: str, voice: str = "", speed: float = 1.0) -> None:
        self._api_key = api_key
        self._voice = voice
        self._speed = speed

    def speak(self, text: str) -> None:
        raise TextToSpeechError("Der Cloud-TTS-Anbieter ist noch nicht konfiguriert.")


class CustomTTS(TextToSpeech):
    """Erweiterungspunkt fuer eine eigene TTS-Implementierung."""

    def speak(self, text: str) -> None:
        raise TextToSpeechError("Der benutzerdefinierte TTS-Anbieter ist nicht implementiert.")


def create_tts(settings: Settings) -> TextToSpeech:
    if settings.tts_provider == "cloud":
        return CloudTTS(api_key=settings.openai_api_key, voice=settings.tts_voice, speed=settings.tts_speed)
    if settings.tts_provider == "custom":
        return CustomTTS()
    return WindowsTTS(voice=settings.tts_voice, speed=settings.tts_speed)
