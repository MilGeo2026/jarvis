from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

from ui.window_controller import WindowMode, apply_window_mode, requires_manual_drag, toggle_always_on_top


def test_requires_manual_drag() -> None:
    assert requires_manual_drag(WindowMode.NORMAL) is False
    assert requires_manual_drag(WindowMode.BORDERLESS) is True
    assert requires_manual_drag(WindowMode.FULLSCREEN) is True
    assert requires_manual_drag(WindowMode.OVERLAY) is True


def test_normal_mode_has_no_frameless_hint() -> None:
    widget = QWidget()
    apply_window_mode(widget, WindowMode.NORMAL)
    assert not (widget.windowFlags() & Qt.WindowType.FramelessWindowHint)
    assert not widget.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    widget.deleteLater()


def test_borderless_mode_sets_frameless_hint() -> None:
    widget = QWidget()
    apply_window_mode(widget, WindowMode.BORDERLESS)
    assert bool(widget.windowFlags() & Qt.WindowType.FramelessWindowHint)
    assert not widget.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    widget.deleteLater()


def test_overlay_mode_sets_translucent_and_always_on_top() -> None:
    widget = QWidget()
    apply_window_mode(widget, WindowMode.OVERLAY)
    flags = widget.windowFlags()
    assert bool(flags & Qt.WindowType.FramelessWindowHint)
    assert bool(flags & Qt.WindowType.WindowStaysOnTopHint)
    assert widget.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    widget.deleteLater()


def test_always_on_top_flag_independent_of_mode() -> None:
    widget = QWidget()
    apply_window_mode(widget, WindowMode.NORMAL, always_on_top=True)
    assert bool(widget.windowFlags() & Qt.WindowType.WindowStaysOnTopHint)
    widget.deleteLater()


def test_toggle_always_on_top() -> None:
    widget = QWidget()
    apply_window_mode(widget, WindowMode.NORMAL)
    toggle_always_on_top(widget, True)
    assert bool(widget.windowFlags() & Qt.WindowType.WindowStaysOnTopHint)
    toggle_always_on_top(widget, False)
    assert not (widget.windowFlags() & Qt.WindowType.WindowStaysOnTopHint)
    widget.deleteLater()
