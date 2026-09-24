"""Zentrale Konfiguration von JARVIS ueber Umgebungsvariablen / .env-Datei."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dotenv ist eine Kernabhaengigkeit
    load_dotenv = None


class ConfigError(Exception):
    """Wird bei ungueltigen (nicht bei fehlenden) Konfigurationswerten geworfen."""


def _bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "ja", "on"}


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str
    anthropic_model: str

    language: str

    stt_provider: str
    stt_local_model: str
    stt_local_device: str
    openai_api_key: str

    tts_provider: str
    tts_voice: str
    tts_speed: float

    wake_word_enabled: bool
    wake_word: str

    log_level: str

    window_mode: str
    always_on_top: bool
    hotkey_toggle: str
    sound_enabled: bool
    boot_sequence_enabled: bool
    theme_path: str

    @classmethod
    def load(cls, env_file: str | Path | None = ".env") -> "Settings":
        if load_dotenv is not None and env_file is not None and Path(env_file).exists():
            load_dotenv(env_file, override=False)

        raw_speed = os.environ.get("TTS_SPEED", "1.0")
        try:
            tts_speed = float(raw_speed)
        except ValueError as exc:
            raise ConfigError(f"TTS_SPEED muss eine Zahl sein, war: {raw_speed!r}") from exc

        stt_provider = os.environ.get("STT_PROVIDER", "local").strip().lower()
        if stt_provider not in {"local", "cloud"}:
            raise ConfigError(f"STT_PROVIDER muss 'local' oder 'cloud' sein, war: {stt_provider!r}")

        tts_provider = os.environ.get("TTS_PROVIDER", "windows").strip().lower()
        if tts_provider not in {"windows", "cloud", "custom"}:
            raise ConfigError(
                f"TTS_PROVIDER muss 'windows', 'cloud' oder 'custom' sein, war: {tts_provider!r}"
            )

        log_level = os.environ.get("LOG_LEVEL", "INFO").strip().upper()
        if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ConfigError(f"LOG_LEVEL ist ungueltig: {log_level!r}")

        window_mode = os.environ.get("WINDOW_MODE", "borderless").strip().lower()
        if window_mode not in {"normal", "borderless", "fullscreen", "overlay"}:
            raise ConfigError(
                f"WINDOW_MODE muss 'normal', 'borderless', 'fullscreen' oder 'overlay' sein, war: {window_mode!r}"
            )

        return cls(
            anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", "").strip(),
            anthropic_model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5").strip(),
            language=os.environ.get("LANGUAGE", "de").strip(),
            stt_provider=stt_provider,
            stt_local_model=os.environ.get("STT_LOCAL_MODEL", "small").strip(),
            stt_local_device=os.environ.get("STT_LOCAL_DEVICE", "cpu").strip(),
            openai_api_key=os.environ.get("OPENAI_API_KEY", "").strip(),
            tts_provider=tts_provider,
            tts_voice=os.environ.get("TTS_VOICE", "").strip(),
            tts_speed=tts_speed,
            wake_word_enabled=_bool(os.environ.get("WAKE_WORD_ENABLED", "true")),
            wake_word=os.environ.get("WAKE_WORD", "jarvis").strip().lower(),
            log_level=log_level,
            window_mode=window_mode,
            always_on_top=_bool(os.environ.get("ALWAYS_ON_TOP", "false")),
            hotkey_toggle=os.environ.get("HOTKEY_TOGGLE", "<ctrl>+<space>").strip(),
            sound_enabled=_bool(os.environ.get("SOUND_ENABLED", "true")),
            boot_sequence_enabled=_bool(os.environ.get("BOOT_SEQUENCE_ENABLED", "true")),
            theme_path=os.environ.get("THEME_PATH", "config/theme.json").strip(),
        )
