import sys
from types import ModuleType
from unittest.mock import MagicMock

import numpy as np
import pytest

from voice.microphone import Microphone, MicrophoneError, RecordingTooShortError


def _fake_sounddevice_module(chunks, port_audio_error=None):
    module = ModuleType("sounddevice")

    class FakePortAudioError(Exception):
        pass

    class FakeInputStream:
        def __init__(self, *args, **kwargs):
            self._chunks = iter(chunks)

        def __enter__(self):
            if port_audio_error:
                raise port_audio_error
            return self

        def __exit__(self, *args):
            return False

        def read(self, frames):
            try:
                chunk = next(self._chunks)
            except StopIteration:
                chunk = np.zeros((frames, 1), dtype="float32")
            return chunk, False

    module.InputStream = FakeInputStream
    module.PortAudioError = FakePortAudioError
    return module


def test_microphone_raises_when_sounddevice_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "sounddevice", None)
    mic = Microphone()
    with pytest.raises(MicrophoneError):
        mic.record_utterance()


def test_microphone_raises_too_short_when_only_silence(monkeypatch: pytest.MonkeyPatch) -> None:
    silence = [np.zeros((1600, 1), dtype="float32") for _ in range(30)]
    monkeypatch.setitem(sys.modules, "sounddevice", _fake_sounddevice_module(silence))
    mic = Microphone(sample_rate=16000)
    with pytest.raises(RecordingTooShortError):
        mic.record_utterance()


def test_microphone_stops_after_speech_and_silence(monkeypatch: pytest.MonkeyPatch) -> None:
    loud = np.ones((1600, 1), dtype="float32") * 0.5
    silence = np.zeros((1600, 1), dtype="float32")
    chunks = [loud, loud] + [silence] * 15
    monkeypatch.setitem(sys.modules, "sounddevice", _fake_sounddevice_module(chunks))
    mic = Microphone(sample_rate=16000)
    audio = mic.record_utterance()
    assert len(audio) > 0


def test_microphone_wraps_port_audio_error(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_module = _fake_sounddevice_module([])
    monkeypatch.setitem(sys.modules, "sounddevice", fake_module)
    mic = Microphone()
    with pytest.raises(MicrophoneError):

        def raising_stream(*args, **kwargs):
            raise fake_module.PortAudioError("kein Geraet")

        fake_module.InputStream = raising_stream
        mic.record_utterance()
