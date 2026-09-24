"""Verwaltet die Fenstermodi (normal/borderless/fullscreen/overlay) eines QWidget-Fensters."""
from __future__ import annotations

from enum import Enum

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget


class WindowMode(str, Enum):
    NORMAL = "normal"
    BORDERLESS = "borderless"
    FULLSCREEN = "fullscreen"
    OVERLAY = "overlay"


def requires_manual_drag(mode: WindowMode) -> bool:
    """Ohne OS-Titelleiste (alle Modi ausser NORMAL) muss das Fenster per Maus verschiebbar sein."""
    return mode != WindowMode.NORMAL


def apply_window_mode(widget: QWidget, mode: WindowMode, always_on_top: bool = False) -> None:
    """Setzt Fenster-Flags passend zum gewuenschten Modus und zeigt das Fenster an.

    OVERLAY macht das Fenster zusaetzlich zum Desktop-Hintergrund echt transparent,
    damit es wie ein HUD ueber anderen Anwendungen schwebt. Die anderen Modi bleiben
    am OS-Fenstermanager "opak" - der Glass-Look entsteht dort rein durch die
    halbtransparenten QML-Panels vor dunklem Hintergrund.
    """
    flags = Qt.WindowType.Window
    if mode in (WindowMode.BORDERLESS, WindowMode.FULLSCREEN, WindowMode.OVERLAY):
        flags |= Qt.WindowType.FramelessWindowHint
    if mode == WindowMode.OVERLAY or always_on_top:
        flags |= Qt.WindowType.WindowStaysOnTopHint

    widget.setWindowFlags(flags)
    widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, mode == WindowMode.OVERLAY)

    if mode == WindowMode.FULLSCREEN:
        widget.showFullScreen()
    else:
        widget.show()


def toggle_always_on_top(widget: QWidget, enabled: bool) -> None:
    flags = widget.windowFlags()
    if enabled:
        flags |= Qt.WindowType.WindowStaysOnTopHint
    else:
        flags &= ~Qt.WindowType.WindowStaysOnTopHint
    was_visible = widget.isVisible()
    widget.setWindowFlags(flags)
    if was_visible:
        widget.show()
