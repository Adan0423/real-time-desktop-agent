from __future__ import annotations


DASHBOARD_STYLE = """
QWidget#rtdaRoot {
    background: #090b0f;
    color: #edf3f8;
    font-family: "Segoe UI";
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
    border-radius: 7px;
}
QFrame#metricTile {
    background: #0d1218;
    border: 1px solid #273240;
    border-radius: 6px;
}
QLabel#appTitle {
    color: #ffffff;
    font-size: 20px;
    font-weight: 800;
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
    padding: 6px 8px;
}
QLabel#statusPill[tone="active"] {
    color: #39d98a;
    border-color: #238a5d;
}
QLabel#statusPill[tone="paused"] {
    color: #ffb24a;
    border-color: #9d6722;
}
QLabel#previewSurface {
    background: #010305;
    color: #c9d6e6;
    border: 1px solid #2a3543;
    border-radius: 7px;
}
QTabWidget::pane {
    border: 0;
}
QTabBar::tab {
    background: #11161d;
    color: #9eaaba;
    border: 1px solid #283442;
    border-radius: 6px;
    padding: 6px 14px;
    margin-right: 6px;
}
QTabBar::tab:selected {
    color: #ffffff;
    border-color: #39d98a;
}
QPushButton {
    background: #171f2a;
    color: #edf5ff;
    border: 1px solid #334258;
    border-radius: 6px;
    min-height: 24px;
    padding: 5px 9px;
}
QPushButton:hover {
    border-color: #39d98a;
    background: #1d2835;
}
QPushButton:pressed {
    background: #243242;
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
    border-radius: 5px;
    min-height: 24px;
    padding: 4px 7px;
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
    spacing: 6px;
}
QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border-radius: 4px;
    border: 1px solid #506278;
    background: #0a0f16;
}
QCheckBox::indicator:checked {
    background: #ffb24a;
    border-color: #ffb24a;
}
"""
