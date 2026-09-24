"""Austauschbare Speech-to-Text-Schnittstelle."""
from __future__ import annotations

import io
import logging
from abc import ABC, abstractmethod
from typing import Any

import numpy as np
import requests
import soundfile as sf

from app.config import Settings

logger = logging.getLogger("jarvis.voice")


class SpeechToTextError(Exception):
    """Deckt: keine Sprache erkannt, API nicht erreichbar, Netzwerkfehler."""


class SpeechToText(ABC):
    @abstractmethod
    def transcribe(self, audio: np.ndarray, sample_rate: int) -> str: ...


class LocalSTT(SpeechToText):
    """Lokales, kostenloses STT mit faster-whisper (laeuft offline)."""

    def __init__(self, model_size: str = "small", device: str = "cpu", language: str = "de") -> None:
        self._model_size = model_size
        self._device = device
        self._language = language
        self._model: Any = None

    def _ensure_model(self) -> Any:
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:
                raise SpeechToTextError("Die lokale Spracherkennung ist nicht installiert.") from exc
            try:
                self._model = WhisperModel(self._model_size, device=self._device, compute_type="int8")
            except Exception as exc:
                raise SpeechToTextError("Das Spracherkennungsmodell konnte nicht geladen werden.") from exc
        return self._model

    def transcribe(self, audio: np.ndarray, sample_rate: int) -> str:
        model = self._ensure_model()
        try:
            segments, _info = model.transcribe(audio, language=self._language)
            text = " ".join(segment.text.strip() for segment in segments).strip()
        except Exception as exc:
            raise SpeechToTextError("Die Sprache konnte nicht erkannt werden.") from exc
        if not text:
            raise SpeechToTextError("Es wurde keine Sprache erkannt.")
        return text


class CloudSTT(SpeechToText):
    """Cloud-STT ueber die OpenAI Whisper-API (Alternative fuer bessere Genauigkeit)."""

    def __init__(self, api_key: str, language: str = "de") -> None:
        self._api_key = api_key
        self._language = language

    def transcribe(self, audio: np.ndarray, sample_rate: int) -> str:
        if not self._api_key:
            raise SpeechToTextError("Fuer die Cloud-Spracherkennung fehlt ein API-Schluessel.")

        buffer = io.BytesIO()
        sf.write(buffer, audio, sample_rate, format="WAV")
        buffer.seek(0)

        try:
            response = requests.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                files={"file": ("audio.wav", buffer, "audio/wav")},
                data={"model": "whisper-1", "language": self._language},
                timeout=20,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise SpeechToTextError("Die Spracherkennung ist momentan nicht erreichbar (Netzwerkfehler).") from exc

        text = response.json().get("text", "").strip()
        if not text:
            raise SpeechToTextError("Es wurde keine Sprache erkannt.")
        return text


def create_stt(settings: Settings) -> SpeechToText:
    if settings.stt_provider == "cloud":
        return CloudSTT(api_key=settings.openai_api_key, language=settings.language)
    return LocalSTT(model_size=settings.stt_local_model, device=settings.stt_local_device, language=settings.language)
