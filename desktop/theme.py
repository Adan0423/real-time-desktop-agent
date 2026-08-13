from __future__ import annotations


DASHBOARD_STYLE = """
QWidget#rtdaRoot {
    background: #090b0f;
    color: #edf3f8;
    font-family: "Segoe UI", system-ui, sans-serif;
    font-size: 12px;
}
QFrame#sidebar {
    background: #0d1117;
    border-right: 1px solid #242d36;
}
QFrame#previewPanel {
    background: #06080b;
}
QFrame#sectionPanel {
    background: #11161d;
    border: 1px solid #283442;
    border-radius: 8px;
}
QFrame#actionBar {
    background: #0f151d;
    border: 1px solid #273240;
    border-radius: 8px;
}
QFrame#inlineRegion {
    background: transparent;
    border: 0;
}
QFrame#metricTile {
    background: #0d1218;
    border: 1px solid #273240;
    border-radius: 6px;
}
QLabel#appTitle {
    color: #ffffff;
    font-size: 19px;
    font-weight: 800;
    letter-spacing: 0.5px;
}
QLabel#sectionTitle,
QLabel#panelTitle {
    color: #ffffff;
    font-size: 13px;
    font-weight: 700;
}
QLabel#fieldLabel,
QLabel#metricLabel,
QLabel#mutedText {
    color: #a2adba;
}
QLabel#metricValue {
    color: #ffb24a;
    font-size: 16px;
    font-weight: 800;
}
QLabel#statusPill {
    background: #161c24;
    color: #b8c4d6;
    border: 1px solid #303b49;
    border-radius: 6px;
    padding: 6px 10px;
    font-weight: 600;
}
QLabel#statusPill[tone="active"] {
    color: #39d98a;
    border-color: #238a5d;
    background: #0d281e;
}
QLabel#statusPill[tone="paused"] {
    color: #ffb24a;
    border-color: #9d6722;
    background: #261b0c;
}
QLabel#previewSurface {
    background: #010305;
    color: #c9d6e6;
    border: 1px solid #2a3543;
    border-radius: 8px;
}
QPushButton#gearButton {
    background: #161d27;
    color: #39d98a;
    border: 1px solid #28374a;
    border-radius: 6px;
    min-width: 32px;
    max-width: 32px;
    min-height: 28px;
    max-height: 28px;
    font-size: 14px;
    padding: 0px;
}
QPushButton#gearButton:hover {
    background: #1f2c3d;
    border-color: #39d98a;
}
QDialog#settingsDialog {
    background: #0d1117;
    color: #edf3f8;
}
QPushButton#navButton {
    background: #11161d;
    color: #9eaaba;
    border: 1px solid #283442;
    border-radius: 6px;
    min-height: 28px;
    padding: 4px 6px;
    font-size: 11px;
    font-weight: 600;
}
QPushButton#navButton:checked {
    color: #ffffff;
    border-color: #39d98a;
    background: #13271f;
}
QPushButton#navButton:hover {
    border-color: #39d98a;
    color: #ffffff;
}
QPushButton {
    background: #171f2a;
    color: #edf5ff;
    border: 1px solid #334258;
    border-radius: 6px;
    min-height: 26px;
    padding: 5px 11px;
    font-weight: 600;
}
QPushButton:hover {
    border-color: #39d98a;
    background: #1e2c3c;
}
QPushButton:pressed {
    background: #25374c;
}
QPushButton:disabled {
    color: #5e6b78;
    background: #111720;
    border-color: #202936;
}
QComboBox,
QLineEdit,
QSpinBox,
QTextEdit {
    background: #070b10;
    color: #ffffff;
    border: 1px solid #2a3646;
    border-radius: 6px;
    min-height: 26px;
    padding: 4px 8px;
    selection-background-color: #276749;
}
QTextEdit {
    min-height: 64px;
}
QComboBox:focus,
QLineEdit:focus,
QSpinBox:focus,
QTextEdit:focus {
    border-color: #39d98a;
}
QCheckBox {
    color: #edf3f8;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 15px;
    height: 15px;
    border-radius: 4px;
    border: 1px solid #506278;
    background: #0a0f16;
}
QCheckBox::indicator:checked {
    background: #39d98a;
    border-color: #39d98a;
}
"""

