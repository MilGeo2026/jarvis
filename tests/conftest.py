import os

import pytest

from app.config import Settings

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication

    _qapp = QApplication.instance() or QApplication([])
except Exception:  # pragma: no cover - Umgebung ohne nutzbares Qt-Backend
    _qapp = None


@pytest.fixture
def base_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-sonnet-5")
    monkeypatch.setenv("LANGUAGE", "de")
    monkeypatch.setenv("STT_PROVIDER", "local")
    monkeypatch.setenv("STT_LOCAL_MODEL", "small")
    monkeypatch.setenv("STT_LOCAL_DEVICE", "cpu")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("TTS_PROVIDER", "windows")
    monkeypatch.setenv("TTS_VOICE", "")
    monkeypatch.setenv("TTS_SPEED", "1.0")
    monkeypatch.setenv("WAKE_WORD_ENABLED", "true")
    monkeypatch.setenv("WAKE_WORD", "jarvis")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("WINDOW_MODE", "borderless")
    monkeypatch.setenv("ALWAYS_ON_TOP", "false")
    monkeypatch.setenv("HOTKEY_TOGGLE", "<ctrl>+<space>")
    monkeypatch.setenv("SOUND_ENABLED", "true")
    monkeypatch.setenv("BOOT_SEQUENCE_ENABLED", "true")
    monkeypatch.setenv("THEME_PATH", "config/theme.json")


@pytest.fixture
def settings(base_env: None) -> Settings:
    return Settings.load(env_file=None)
