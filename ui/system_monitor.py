"""Pollt leichte Systemkennzahlen (CPU/RAM/Netzwerk/GPU) fuer die dezente Seitenanzeige.

Bewusst mit niedriger Frequenz (Standard: alle 2 Sekunden), um im Leerlauf
keine unnoetige CPU-Last zu verursachen.
"""
from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QTimer

from ui.bridge import JarvisBridge

logger = logging.getLogger("jarvis.ui")

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None

POLL_INTERVAL_MS = 2000


def _network_online() -> bool:
    """Guenstige, nicht-blockierende Naeherung: mindestens eine aktive Netzwerkschnittstelle
    ausser Loopback. Prueft keine echte Internetverbindung, um die UI nicht zu blockieren."""
    if psutil is None:
        return True
    try:
        stats = psutil.net_if_stats()
    except OSError:
        return True
    return any(info.isup for name, info in stats.items() if name != "lo")


def _gpu_percent() -> float | None:
    try:
        import pynvml

        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        usage = pynvml.nvmlDeviceGetUtilizationRates(handle)
        return float(usage.gpu)
    except Exception:
        return None


class SystemMonitor(QObject):
    """Aktualisiert die JarvisBridge periodisch mit Systemkennzahlen."""

    def __init__(self, bridge: JarvisBridge, interval_ms: int = POLL_INTERVAL_MS, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._bridge = bridge
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._timer.setInterval(interval_ms)

    def start(self) -> None:
        self._poll()
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def _poll(self) -> None:
        cpu = psutil.cpu_percent(interval=None) if psutil else 0.0
        ram = psutil.virtual_memory().percent if psutil else 0.0
        gpu = _gpu_percent()
        online = _network_online()
        self._bridge.update_system_stats(cpu, ram, gpu, online)
