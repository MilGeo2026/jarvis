from unittest.mock import MagicMock

import numpy as np

from voice.microphone import MicrophoneError, RecordingTooShortError
from voice.wake_word import WakeWordDetector


def _make_detector(transcribed_text: str = "", enabled: bool = True) -> WakeWordDetector:
    microphone = MagicMock()
    microphone.record_utterance.return_value = np.zeros(16000, dtype="float32")
    microphone.sample_rate = 16000
    stt = MagicMock()
    stt.transcribe.return_value = transcribed_text
    return WakeWordDetector(wake_word="jarvis", stt=stt, microphone=microphone, enabled=enabled)


def test_wake_word_detected() -> None:
    detector = _make_detector("Hey Jarvis, wie geht es dir?")
    assert detector.listen_once() is True


def test_wake_word_not_detected() -> None:
    detector = _make_detector("Wie ist das Wetter heute?")
    assert detector.listen_once() is False


def test_wake_word_disabled_returns_false_without_listening() -> None:
    detector = _make_detector("Jarvis", enabled=False)
    assert detector.listen_once() is False


def test_wake_word_handles_microphone_error() -> None:
    microphone = MagicMock()
    microphone.record_utterance.side_effect = MicrophoneError("kein Mikrofon")
    stt = MagicMock()
    detector = WakeWordDetector("jarvis", stt, microphone, enabled=True)
    assert detector.listen_once() is False


def test_wake_word_handles_too_short_recording() -> None:
    microphone = MagicMock()
    microphone.record_utterance.side_effect = RecordingTooShortError("zu kurz")
    stt = MagicMock()
    detector = WakeWordDetector("jarvis", stt, microphone, enabled=True)
    assert detector.listen_once() is False
