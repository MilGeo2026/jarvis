from app.events import ActivityBus, AudioLevelBus
from app.state import AssistantState, StateManager
from ui.bridge import JarvisBridge
from ui.theme import Theme


def make_bridge() -> tuple[JarvisBridge, StateManager, ActivityBus, AudioLevelBus]:
    theme = Theme(primary_color="#ABCDEF")
    state_manager = StateManager()
    activity_bus = ActivityBus()
    audio_level_bus = AudioLevelBus()
    bridge = JarvisBridge(theme, state_manager, activity_bus, audio_level_bus, boot_sequence_enabled=True)
    return bridge, state_manager, activity_bus, audio_level_bus


def test_bridge_reflects_initial_state() -> None:
    bridge, state_manager, _, _ = make_bridge()
    assert bridge.state == AssistantState.STANDBY.value
    assert bridge.showBoot is True


def test_bridge_updates_on_state_change() -> None:
    bridge, state_manager, _, _ = make_bridge()
    received = []
    bridge.stateChanged.connect(received.append)

    state_manager.set(AssistantState.LISTENING)

    assert bridge.state == "LISTENING"
    assert received == ["LISTENING"]


def test_bridge_updates_on_activity_text() -> None:
    bridge, _, activity_bus, _ = make_bridge()
    activity_bus.publish("Oeffne YouTube ...")
    assert bridge.activityText == "Oeffne YouTube ..."


def test_bridge_updates_on_mic_level() -> None:
    bridge, _, _, audio_level_bus = make_bridge()
    audio_level_bus.publish(0.73)
    assert bridge.micLevel == 0.73


def test_bridge_system_stats() -> None:
    bridge, _, _, _ = make_bridge()
    bridge.update_system_stats(cpu=12.5, ram=40.0, gpu=None, network_online=False)
    assert bridge.cpuPercent == 12.5
    assert bridge.ramPercent == 40.0
    assert bridge.gpuPercent == -1.0
    assert bridge.networkOnline is False


def test_bridge_boot_status_and_hide() -> None:
    bridge, _, _, _ = make_bridge()
    bridge.set_boot_status(voice_online=True, ai_online=True, mic_online=False, tools_online=True)
    assert bridge.voiceOnline is True
    assert bridge.aiOnline is True
    assert bridge.micOnline is False
    assert bridge.toolsOnline is True

    bridge.hide_boot()
    assert bridge.showBoot is False


def test_bridge_theme_properties_are_constant() -> None:
    bridge, _, _, _ = make_bridge()
    assert bridge.primaryColor == "#ABCDEF"
    assert bridge.glowEnabled is True


def test_bridge_submit_text_emits_signal() -> None:
    bridge, _, _, _ = make_bridge()
    received = []
    bridge.textSubmitted.connect(received.append)

    bridge.submitText("  Wie spaet ist es?  ")
    bridge.submitText("   ")

    assert received == ["Wie spaet ist es?"]
