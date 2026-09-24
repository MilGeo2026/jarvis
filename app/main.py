"""Einstiegspunkt von JARVIS: verbindet Konfiguration, KI, Tools und (optional) GUI/Voice."""
from __future__ import annotations

import argparse
import logging
import sys

from ai.claude_client import ClaudeClient
from ai.conversation import ConversationManager
from app.config import ConfigError, Settings
from app.events import ActivityBus, AudioLevelBus
from app.orchestrator import Assistant
from app.state import StateManager
from security.confirmation import SecurityGuard
from tools import build_default_registry
from voice.pipeline import VoiceComponents

logger = logging.getLogger("jarvis")


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level, logging.INFO), format="[%(levelname)s] %(message)s")


def build_assistant(settings: Settings) -> tuple[Assistant, StateManager, ActivityBus]:
    state_manager = StateManager()
    activity_bus = ActivityBus()
    tool_registry = build_default_registry()
    claude_client = ClaudeClient(settings, tool_registry)
    conversation = ConversationManager()
    security_guard = SecurityGuard()
    assistant = Assistant(claude_client, tool_registry, conversation, security_guard, state_manager, activity_bus)
    return assistant, state_manager, activity_bus


def build_voice_components(settings: Settings) -> VoiceComponents:
    from voice.microphone import Microphone
    from voice.speech_to_text import create_stt
    from voice.text_to_speech import create_tts
    from voice.wake_word import WakeWordDetector

    microphone = Microphone()
    stt = create_stt(settings)
    tts = create_tts(settings)
    wake_word = WakeWordDetector(settings.wake_word, stt, microphone, enabled=settings.wake_word_enabled)
    return VoiceComponents(microphone=microphone, stt=stt, tts=tts, wake_word=wake_word)


def run_text_mode(assistant: Assistant) -> None:
    print("JARVIS (Text-Modus). 'exit' zum Beenden.")
    while True:
        try:
            user_input = input("Du: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if user_input.lower() in {"exit", "quit", "ende"}:
            break
        if not user_input:
            continue
        reply = assistant.handle_text(user_input)
        print(f"JARVIS: {reply}")


def run_gui_mode(assistant: Assistant, state_manager: StateManager, activity_bus: ActivityBus, settings: Settings) -> int:
    from PySide6.QtWidgets import QApplication

    from ui.bridge import JarvisBridge
    from ui.hotkey import GlobalHotkey
    from ui.main_window import JarvisWindow
    from ui.sound import SoundPlayer
    from ui.system_monitor import SystemMonitor
    from ui.theme import Theme
    from ui.window_controller import WindowMode

    audio_level_bus = AudioLevelBus()
    theme = Theme.load(settings.theme_path)

    voice_components: VoiceComponents | None = None
    try:
        voice_components = build_voice_components(settings)
    except Exception:
        logger.warning("Sprachfunktionen konnten nicht initialisiert werden, GUI startet ohne Voice.")

    app = QApplication.instance() or QApplication([])

    bridge = JarvisBridge(
        theme=theme,
        state_manager=state_manager,
        activity_bus=activity_bus,
        audio_level_bus=audio_level_bus,
        boot_sequence_enabled=settings.boot_sequence_enabled,
    )
    bridge.set_boot_status(
        voice_online=voice_components is not None,
        ai_online=bool(settings.anthropic_api_key),
        mic_online=voice_components is not None,
        tools_online=True,
    )

    sound = SoundPlayer(enabled=settings.sound_enabled)

    window = JarvisWindow(
        assistant=assistant,
        bridge=bridge,
        state_manager=state_manager,
        activity_bus=activity_bus,
        audio_level_bus=audio_level_bus,
        sound=sound,
        window_mode=WindowMode(settings.window_mode),
        always_on_top=settings.always_on_top,
        voice_components=voice_components,
        wake_word_enabled=settings.wake_word_enabled,
    )

    if settings.boot_sequence_enabled:
        window.finish_boot_sequence()
    else:
        sound.play_online()

    monitor = SystemMonitor(bridge)
    monitor.start()

    hotkey = GlobalHotkey(settings.hotkey_toggle)
    hotkey.activated.connect(window.toggle_visibility)
    hotkey.start()

    exit_code = app.exec()
    hotkey.stop()
    monitor.stop()
    return exit_code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="JARVIS - persoenlicher Sprachassistent")
    parser.add_argument("--mode", choices=["gui", "text"], default="gui", help="Betriebsmodus")
    args = parser.parse_args(argv)

    try:
        settings = Settings.load()
    except ConfigError as exc:
        print(f"Konfigurationsfehler: {exc}")
        return 1

    configure_logging(settings.log_level)
    logger.info("JARVIS gestartet")

    assistant, state_manager, activity_bus = build_assistant(settings)

    if args.mode == "text":
        run_text_mode(assistant)
        return 0

    return run_gui_mode(assistant, state_manager, activity_bus, settings)


if __name__ == "__main__":
    sys.exit(main())
