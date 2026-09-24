"""Verbindet den echten Assistenten-Zustand (StateManager/ActivityBus/AudioLevelBus)
mit der QML-Oberflaeche. Die GUI liest ausschliesslich diese Properties - sie
animiert nie unabhaengig vom tatsaechlichen Systemzustand."""
from __future__ import annotations

from PySide6.QtCore import Property, QObject, Signal, Slot

from app.events import ActivityBus, AudioLevelBus
from app.state import AssistantState, StateManager
from ui.theme import Theme


class JarvisBridge(QObject):
    stateChanged = Signal(str)
    activityTextChanged = Signal(str)
    micLevelChanged = Signal(float)
    systemStatsChanged = Signal()
    bootStatusChanged = Signal()
    showBootChanged = Signal(bool)
    textSubmitted = Signal(str)

    def __init__(
        self,
        theme: Theme,
        state_manager: StateManager,
        activity_bus: ActivityBus,
        audio_level_bus: AudioLevelBus,
        boot_sequence_enabled: bool = True,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._theme = theme
        self._state = state_manager.state.value
        self._activity_text = activity_bus.value
        self._mic_level = audio_level_bus.value

        self._cpu_percent = 0.0
        self._ram_percent = 0.0
        self._gpu_percent = -1.0
        self._network_online = True

        self._voice_online = False
        self._ai_online = False
        self._mic_online = False
        self._tools_online = False
        self._system_online = True
        self._show_boot = boot_sequence_enabled

        state_manager.subscribe(self._on_state_changed)
        activity_bus.subscribe(self._on_activity_changed)
        audio_level_bus.subscribe(self._on_mic_level_changed)

    # -- Bus-Callbacks (koennen aus einem Hintergrund-Thread aufgerufen werden) --

    def _on_state_changed(self, state: AssistantState) -> None:
        self._state = state.value
        self.stateChanged.emit(self._state)

    def _on_activity_changed(self, text: str) -> None:
        self._activity_text = text
        self.activityTextChanged.emit(text)

    def _on_mic_level_changed(self, level: float) -> None:
        self._mic_level = level
        self.micLevelChanged.emit(level)

    # -- Von aussen aufgerufen (SystemMonitor, main.py) --

    def update_system_stats(self, cpu: float, ram: float, gpu: float | None, network_online: bool) -> None:
        self._cpu_percent = cpu
        self._ram_percent = ram
        self._gpu_percent = gpu if gpu is not None else -1.0
        self._network_online = network_online
        self.systemStatsChanged.emit()

    def set_boot_status(self, voice_online: bool, ai_online: bool, mic_online: bool, tools_online: bool) -> None:
        self._voice_online = voice_online
        self._ai_online = ai_online
        self._mic_online = mic_online
        self._tools_online = tools_online
        self.bootStatusChanged.emit()

    def hide_boot(self) -> None:
        if self._show_boot:
            self._show_boot = False
            self.showBootChanged.emit(False)

    # -- Von QML aufgerufen --

    @Slot(str)
    def submitText(self, text: str) -> None:
        if text.strip():
            self.textSubmitted.emit(text.strip())

    # -- Qt Properties fuer QML-Bindings --

    state = Property(str, lambda self: self._state, notify=stateChanged)
    activityText = Property(str, lambda self: self._activity_text, notify=activityTextChanged)
    micLevel = Property(float, lambda self: self._mic_level, notify=micLevelChanged)

    cpuPercent = Property(float, lambda self: self._cpu_percent, notify=systemStatsChanged)
    ramPercent = Property(float, lambda self: self._ram_percent, notify=systemStatsChanged)
    gpuPercent = Property(float, lambda self: self._gpu_percent, notify=systemStatsChanged)
    networkOnline = Property(bool, lambda self: self._network_online, notify=systemStatsChanged)

    voiceOnline = Property(bool, lambda self: self._voice_online, notify=bootStatusChanged)
    aiOnline = Property(bool, lambda self: self._ai_online, notify=bootStatusChanged)
    micOnline = Property(bool, lambda self: self._mic_online, notify=bootStatusChanged)
    toolsOnline = Property(bool, lambda self: self._tools_online, notify=bootStatusChanged)
    systemOnline = Property(bool, lambda self: self._system_online, notify=bootStatusChanged)

    showBoot = Property(bool, lambda self: self._show_boot, notify=showBootChanged)

    # Theme-Properties aendern sich zur Laufzeit nicht, daher ohne NOTIFY-Signal (constant).
    primaryColor = Property(str, lambda self: self._theme.primary_color, constant=True)
    secondaryColor = Property(str, lambda self: self._theme.secondary_color, constant=True)
    errorColor = Property(str, lambda self: self._theme.error_color, constant=True)
    backgroundColor = Property(str, lambda self: self._theme.background_color, constant=True)
    backgroundOpacity = Property(float, lambda self: self._theme.background_opacity, constant=True)
    textColor = Property(str, lambda self: self._theme.text_color, constant=True)
    fontFamily = Property(str, lambda self: self._theme.font_family, constant=True)
    glowEnabled = Property(bool, lambda self: self._theme.glow, constant=True)
    animationsEnabled = Property(bool, lambda self: self._theme.animations, constant=True)
