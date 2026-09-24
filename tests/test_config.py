import pytest

from app.config import ConfigError, Settings


def test_settings_load_reads_env(settings: Settings) -> None:
    assert settings.anthropic_api_key == "test-key"
    assert settings.anthropic_model == "claude-sonnet-5"
    assert settings.stt_provider == "local"
    assert settings.tts_provider == "windows"
    assert settings.wake_word == "jarvis"
    assert settings.wake_word_enabled is True
    assert settings.tts_speed == 1.0


def test_settings_missing_api_key_does_not_raise(base_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    settings = Settings.load(env_file=None)
    assert settings.anthropic_api_key == ""


def test_invalid_tts_speed_raises(base_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TTS_SPEED", "schnell")
    with pytest.raises(ConfigError):
        Settings.load(env_file=None)


def test_invalid_stt_provider_raises(base_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STT_PROVIDER", "telepathy")
    with pytest.raises(ConfigError):
        Settings.load(env_file=None)


def test_invalid_tts_provider_raises(base_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TTS_PROVIDER", "magic")
    with pytest.raises(ConfigError):
        Settings.load(env_file=None)


def test_invalid_log_level_raises(base_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "VERY_LOUD")
    with pytest.raises(ConfigError):
        Settings.load(env_file=None)


def test_wake_word_disabled(base_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WAKE_WORD_ENABLED", "false")
    settings = Settings.load(env_file=None)
    assert settings.wake_word_enabled is False
