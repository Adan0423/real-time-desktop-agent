from __future__ import annotations

FLOATING_PALETTE = {
    "background": "#0B0F14",
    "surface": "#111821",
    "surface_hover": "#17212B",
    "border": "#263443",
    "text_primary": "#F2F5F7",
    "text_secondary": "#9AA8B6",
    "accent": "#26D7D0",
    "success": "#29D98F",
    "warning": "#F4C95D",
    "danger": "#F35D7A",
}

FLOATING_STYLE = """
QWidget#floatingRoot {
    background-color: transparent;
    color: #F2F5F7;
    font-family: "Segoe UI", system-ui, sans-serif;
    font-size: 11px;
}
QFrame#collapsedCard {
    background-color: #0B0F14;
    border: 1px solid #263443;
    border-radius: 16px;
}
QFrame#expandedPanel {
    background-color: #111821;
    border: 1px solid #263443;
    border-radius: 16px;
}
QLabel#floatingTitle {
    color: #FFFFFF;
    font-size: 13px;
    font-weight: 700;
}
QLabel#floatingSubtitle {
    color: #9AA8B6;
    font-size: 10px;
}
QLabel#floatingMetrics {
    color: #26D7D0;
    font-size: 12px;
    font-weight: 600;
}
QPushButton#actionStartButton {
    background: #132b26;
    color: #29D98F;
    border: 1px solid #1e5c46;
    border-radius: 10px;
    padding: 6px 10px;
    font-weight: 700;
    min-height: 28px;
}
QPushButton#actionStartButton:hover {
    background: #1b3d36;
    border-color: #29D98F;
}
QPushButton#actionPauseButton {
    background: #2b2413;
    color: #F4C95D;
    border: 1px solid #5c4a1e;
    border-radius: 10px;
    padding: 6px 10px;
    font-weight: 700;
    min-height: 28px;
}
QPushButton#actionPauseButton:hover {
    background: #3d331b;
    border-color: #F4C95D;
}
QPushButton#actionStopButton {
    background: #2b1318;
    color: #F35D7A;
    border: 1px solid #5c1e28;
    border-radius: 10px;
    padding: 6px 10px;
    font-weight: 700;
    min-height: 28px;
}
QPushButton#actionStopButton:hover {
    background: #3d1b22;
    border-color: #F35D7A;
}
QPushButton#utilityButton {
    background: #17212B;
    color: #F2F5F7;
    border: 1px solid #263443;
    border-radius: 10px;
    padding: 6px 10px;
    font-weight: 600;
    min-height: 28px;
}
QPushButton#utilityButton:hover {
    background: #202d3b;
    border-color: #26D7D0;
}
QPushButton#iconOnlyButton {
    background: transparent;
    color: #9AA8B6;
    border: none;
    font-size: 13px;
    padding: 2px;
}
QPushButton#iconOnlyButton:hover {
    color: #26D7D0;
}
QPushButton#toggleExpandButton {
    background: #17212B;
    color: #26D7D0;
    border: 1px solid #263443;
    border-radius: 8px;
    font-size: 10px;
    font-weight: bold;
    min-height: 22px;
}
QPushButton#toggleExpandButton:hover {
    background: #202d3b;
    border-color: #26D7D0;
}
"""
