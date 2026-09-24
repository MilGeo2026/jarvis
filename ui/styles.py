"""Dunkles, futuristisches JARVIS-Theme."""

STATE_COLORS = {
    "IDLE": "#3b82f6",
    "LISTENING": "#22d3ee",
    "THINKING": "#facc15",
    "SPEAKING": "#4ade80",
    "ERROR": "#f87171",
}

STYLESHEET = """
QWidget {
    background-color: #0b0f19;
    color: #e2e8f0;
    font-family: "Segoe UI", sans-serif;
    font-size: 14px;
}

QLabel#title {
    font-size: 28px;
    font-weight: 600;
    letter-spacing: 4px;
    color: #38bdf8;
    padding: 12px 0;
}

QLabel#stateLabel {
    font-size: 13px;
    letter-spacing: 2px;
    color: #94a3b8;
    padding-left: 6px;
}

QTextEdit#transcript {
    background-color: #111827;
    border: 1px solid #1f2937;
    border-radius: 10px;
    padding: 10px;
}

QLineEdit {
    background-color: #111827;
    border: 1px solid #1f2937;
    border-radius: 8px;
    padding: 8px;
}

QPushButton {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 14px;
}

QPushButton:hover {
    background-color: #273549;
}

QPushButton:checked {
    background-color: #0ea5e9;
    color: #0b0f19;
}
"""
