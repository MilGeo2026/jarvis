import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest

from app.config import Settings
from voice.text_to_speech import CloudTTS, CustomTTS, TextToSpeechError, WindowsTTS, create_tts


def _fake_pyttsx3_module(engine: MagicMock) -> ModuleType:
    module = ModuleType("pyttsx3")
    module.init = MagicMock(return_value=engine)
    return module


def _make_fake_engine() -> MagicMock:
    engine = MagicMock()
    engine.getProperty.side_effect = lambda name: 200 if name == "rate" else []
    return engine


def test_windows_tts_speaks_text(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = _make_fake_engine()
    monkeypatch.setitem(sys.modules, "pyttsx3", _fake_pyttsx3_module(engine))

    tts = WindowsTTS(voice="", speed=1.0)
    tts.speak("Natuerlich.")

    engine.say.assert_called_once_with("Natuerlich.")
    engine.runAndWait.assert_called_once()


def test_windows_tts_ignores_empty_text(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = _make_fake_engine()
    monkeypatch.setitem(sys.modules, "pyttsx3", _fake_pyttsx3_module(engine))

    tts = WindowsTTS()
    tts.speak("   ")

    engine.say.assert_not_called()


def test_windows_tts_raises_when_library_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "pyttsx3", None)
    tts = WindowsTTS()
    with pytest.raises(TextToSpeechError):
        tts.speak("Hallo")


def test_windows_tts_wraps_engine_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = _make_fake_engine()
    engine.say.side_effect = RuntimeError("boom")
    monkeypatch.setitem(sys.modules, "pyttsx3", _fake_pyttsx3_module(engine))

    tts = WindowsTTS()
    with pytest.raises(TextToSpeechError):
        tts.speak("Hallo")


def test_cloud_tts_not_configured() -> None:
    with pytest.raises(TextToSpeechError):
        CloudTTS(api_key="").speak("Hallo")


def test_custom_tts_not_implemented() -> None:
    with pytest.raises(TextToSpeechError):
        CustomTTS().speak("Hallo")


def test_create_tts_factory_windows(settings: Settings) -> None:
    assert isinstance(create_tts(settings), WindowsTTS)


def test_create_tts_factory_cloud(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TTS_PROVIDER", "cloud")
    cloud_settings = Settings.load(env_file=None)
    assert isinstance(create_tts(cloud_settings), CloudTTS)


def test_create_tts_factory_custom(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TTS_PROVIDER", "custom")
    custom_settings = Settings.load(env_file=None)
    assert isinstance(create_tts(custom_settings), CustomTTS)
