import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.config import Settings
from voice.speech_to_text import CloudSTT, LocalSTT, SpeechToTextError, create_stt


def _fake_whisper_module(segments):
    module = ModuleType("faster_whisper")

    class FakeWhisperModel:
        def __init__(self, *args, **kwargs):
            pass

        def transcribe(self, audio, language):
            return segments, SimpleNamespace(language=language)

    module.WhisperModel = FakeWhisperModel
    return module


def test_local_stt_returns_transcribed_text(monkeypatch: pytest.MonkeyPatch) -> None:
    segments = [SimpleNamespace(text=" Hallo "), SimpleNamespace(text="Welt ")]
    monkeypatch.setitem(sys.modules, "faster_whisper", _fake_whisper_module(segments))

    stt = LocalSTT(model_size="small", device="cpu")
    text = stt.transcribe(np.zeros(16000, dtype="float32"), 16000)

    assert text == "Hallo Welt"


def test_local_stt_raises_when_no_speech_detected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "faster_whisper", _fake_whisper_module([]))
    stt = LocalSTT()
    with pytest.raises(SpeechToTextError):
        stt.transcribe(np.zeros(16000, dtype="float32"), 16000)


def test_local_stt_raises_when_library_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "faster_whisper", None)
    stt = LocalSTT()
    with pytest.raises(SpeechToTextError):
        stt.transcribe(np.zeros(16000, dtype="float32"), 16000)


def test_cloud_stt_without_key_raises() -> None:
    stt = CloudSTT(api_key="")
    with pytest.raises(SpeechToTextError):
        stt.transcribe(np.zeros(16000, dtype="float32"), 16000)


def test_cloud_stt_success() -> None:
    stt = CloudSTT(api_key="test-key")
    fake_response = MagicMock()
    fake_response.json.return_value = {"text": "Hallo Jarvis"}
    fake_response.raise_for_status.return_value = None

    with patch("voice.speech_to_text.requests.post", return_value=fake_response):
        text = stt.transcribe(np.zeros(16000, dtype="float32"), 16000)

    assert text == "Hallo Jarvis"


def test_cloud_stt_network_error() -> None:
    import requests

    stt = CloudSTT(api_key="test-key")
    with patch("voice.speech_to_text.requests.post", side_effect=requests.ConnectionError("down")):
        with pytest.raises(SpeechToTextError):
            stt.transcribe(np.zeros(16000, dtype="float32"), 16000)


def test_create_stt_factory_local(settings: Settings) -> None:
    stt = create_stt(settings)
    assert isinstance(stt, LocalSTT)


def test_create_stt_factory_cloud(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STT_PROVIDER", "cloud")
    cloud_settings = Settings.load(env_file=None)
    stt = create_stt(cloud_settings)
    assert isinstance(stt, CloudSTT)
