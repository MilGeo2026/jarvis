from unittest.mock import MagicMock

import numpy as np

from app.events import ActivityBus, AudioLevelBus
from app.state import AssistantState, StateManager
from voice.microphone import MicrophoneError
from voice.pipeline import VoicePipeline


def make_pipeline(on_user_text=None, wake_enabled: bool = True):
    microphone = MagicMock()
    microphone.record_utterance.return_value = np.zeros(16000, dtype="float32")
    microphone.sample_rate = 16000
    stt = MagicMock()
    stt.transcribe.return_value = "Wie spaet ist es?"
    tts = MagicMock()
    wake_word = MagicMock()
    wake_word.enabled = wake_enabled
    state_manager = StateManager()
    activity_bus = ActivityBus()
    audio_level_bus = AudioLevelBus()

    pipeline = VoicePipeline(
        microphone=microphone,
        stt=stt,
        tts=tts,
        wake_word=wake_word,
        state_manager=state_manager,
        on_user_text=on_user_text or (lambda text: "Es ist 14 Uhr."),
        activity_bus=activity_bus,
        audio_level_bus=audio_level_bus,
    )
    return pipeline, microphone, stt, tts, wake_word, state_manager, activity_bus, audio_level_bus


def test_listen_and_respond_once_publishes_recognized_text_and_reply() -> None:
    pipeline, *_rest, state_manager, activity_bus, audio_level_bus = make_pipeline()

    reply = pipeline.listen_and_respond_once()

    assert reply == "Es ist 14 Uhr."
    assert state_manager.state == AssistantState.STANDBY
    assert audio_level_bus.value == 0.0  # nach Aufnahme wieder zurueckgesetzt


def test_listen_and_respond_once_passes_level_callback_to_microphone() -> None:
    pipeline, microphone, *_ = make_pipeline()
    pipeline.listen_and_respond_once()
    _, kwargs = microphone.record_utterance.call_args
    assert callable(kwargs["on_level"])


def test_microphone_error_sets_error_then_standby_and_speaks_message() -> None:
    pipeline, microphone, stt, tts, *_rest, state_manager, activity_bus, _ = make_pipeline()
    microphone.record_utterance.side_effect = MicrophoneError("Ich kann dein Mikrofon momentan nicht erreichen.")

    result = pipeline.listen_and_respond_once()

    assert result is None
    assert state_manager.state == AssistantState.STANDBY
    tts.speak.assert_called_once_with("Ich kann dein Mikrofon momentan nicht erreichen.")


def test_run_forever_calls_on_wake_detected_when_wake_word_triggers() -> None:
    on_wake = MagicMock()
    pipeline, microphone, stt, tts, wake_word, state_manager, *_ = make_pipeline(
        on_user_text=lambda text: "Natuerlich."
    )
    pipeline._on_wake_detected = on_wake
    wake_word.listen_for_activation.side_effect = [(True, "")]

    call_count = {"n": 0}

    def stop_after_one(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] >= 1:
            pipeline.stop()
        return "Natuerlich."

    pipeline._on_user_text = stop_after_one

    pipeline.run_forever()

    on_wake.assert_called_once()


def test_run_forever_uses_command_said_in_same_breath_as_wake_word() -> None:
    """"Jarvis, wie spaet ist es?" in einem Atemzug darf keine zweite, leere
    Aufnahme ausloesen (frueherer Bug: die Frage ging dabei verloren)."""
    pipeline, microphone, stt, tts, wake_word, state_manager, activity_bus, _ = make_pipeline()
    wake_word.listen_for_activation.side_effect = [(True, "wie spaet ist es?")]

    received_texts = []

    def stop_after_one(text: str) -> str:
        received_texts.append(text)
        pipeline.stop()
        return "Es ist 14 Uhr."

    pipeline._on_user_text = stop_after_one

    pipeline.run_forever()

    assert received_texts == ["wie spaet ist es?"]
    microphone.record_utterance.assert_not_called()
    assert activity_bus.value == "Es ist 14 Uhr."
    assert state_manager.state == AssistantState.STANDBY
