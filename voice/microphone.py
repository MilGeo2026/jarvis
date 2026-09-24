"""Mikrofon-Zugriff und Aufnahme mit einfacher Stille-Erkennung."""
from __future__ import annotations

import logging

import numpy as np

logger = logging.getLogger("jarvis.voice")

SAMPLE_RATE = 16000
SILENCE_THRESHOLD = 0.01
SILENCE_DURATION_S = 1.2
MAX_RECORDING_S = 15
MIN_RECORDING_S = 0.4


class MicrophoneError(Exception):
    """Wird geworfen, wenn kein Mikrofon verfuegbar ist oder die Aufnahme fehlschlaegt."""


class RecordingTooShortError(Exception):
    """Die Aufnahme war zu kurz, um sinnvoll transkribiert zu werden."""


class Microphone:
    """Nimmt Audio auf, bis eine Sprechpause erkannt wird oder die Maximaldauer erreicht ist."""

    def __init__(self, sample_rate: int = SAMPLE_RATE) -> None:
        self.sample_rate = sample_rate

    def _chunk_duration(self) -> float:
        return 0.1

    def record_utterance(self) -> np.ndarray:
        try:
            import sounddevice as sd
        except (ImportError, OSError) as exc:
            raise MicrophoneError("Ich kann dein Mikrofon momentan nicht erreichen.") from exc

        chunk_frames = int(self._chunk_duration() * self.sample_rate)
        silence_chunks_needed = int(SILENCE_DURATION_S / self._chunk_duration())
        max_chunks = int(MAX_RECORDING_S / self._chunk_duration())

        frames: list[np.ndarray] = []
        silent_run = 0
        has_spoken = False

        try:
            with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype="float32") as stream:
                for _ in range(max_chunks):
                    chunk, _ = stream.read(chunk_frames)
                    chunk = chunk.reshape(-1)
                    frames.append(chunk)
                    volume = float(np.sqrt(np.mean(np.square(chunk)))) if len(chunk) else 0.0

                    if volume >= SILENCE_THRESHOLD:
                        has_spoken = True
                        silent_run = 0
                    else:
                        silent_run += 1

                    if has_spoken and silent_run >= silence_chunks_needed:
                        break
        except sd.PortAudioError as exc:
            raise MicrophoneError("Ich kann dein Mikrofon momentan nicht erreichen.") from exc

        audio = np.concatenate(frames) if frames else np.array([], dtype="float32")
        duration = len(audio) / self.sample_rate
        if duration < MIN_RECORDING_S or not has_spoken:
            raise RecordingTooShortError("Die Aufnahme war zu kurz oder es wurde nichts gesagt.")
        return audio
