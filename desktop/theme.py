from __future__ import annotations


DASHBOARD_STYLE = """
QWidget#rtdaRoot {
    background: #080c14;
    color: #f8fafc;
    font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
    font-size: 12px;
}
QFrame#sidebar {
    background: #0c121e;
    border-right: 1px solid #1e293b;
}
QFrame#previewPanel {
    background: #060911;
}
QFrame#sectionPanel {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 12px;
}
QFrame#actionBar {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 12px;
}
QFrame#inlineRegion {
    background: transparent;
    border: 0;
}
QFrame#metricTile {
    background: #0a101d;
    border: 1px solid #1e293b;
    border-radius: 10px;
}
QLabel#appTitle {
    color: #ffffff;
    font-size: 20px;
    font-weight: 900;
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
    color: #94a3b8;
    font-size: 11px;
}
QLabel#metricValue {
    color: #38bdf8;
    font-size: 16px;
    font-weight: 800;
}
QLabel#statusPill {
    background: #0f172a;
    color: #94a3b8;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 6px 12px;
    font-weight: 600;
}
QLabel#statusPill[tone="active"] {
    color: #34d399;
    border-color: #10b981;
    background: #064e3b;
    font-weight: 700;
}
QLabel#statusPill[tone="paused"] {
    color: #fbbf24;
    border-color: #f59e0b;
    background: #451a03;
    font-weight: 700;
}
QLabel#previewSurface {
    background: #020617;
    color: #94a3b8;
    border: 1.5px solid #1e293b;
    border-radius: 14px;
}
QPushButton#gearButton {
    background: #0f172a;
    color: #34d399;
    border: 1px solid #1e293b;
    border-radius: 8px;
    min-width: 34px;
    max-width: 34px;
    min-height: 30px;
    max-height: 30px;
    font-size: 15px;
    padding: 0px;
}
QPushButton#gearButton:hover {
    background: #1e293b;
    border-color: #10b981;
    color: #ffffff;
}
QDialog#settingsDialog {
    background: #0c121e;
    color: #f8fafc;
}
QPushButton#navButton {
    background: #0f172a;
    color: #94a3b8;
    border: 1px solid #1e293b;
    border-radius: 8px;
    min-height: 30px;
    padding: 4px 8px;
    font-size: 11px;
    font-weight: 600;
}
QPushButton#navButton:checked {
    color: #ffffff;
    border: 1.5px solid #10b981;
    background: #064e3b;
    font-weight: 700;
}
QPushButton#navButton:hover {
    border-color: #38bdf8;
    color: #ffffff;
    background: #1e293b;
}
QPushButton {
    background: #0f172a;
    color: #f8fafc;
    border: 1px solid #1e293b;
    border-radius: 8px;
    min-height: 28px;
    padding: 6px 12px;
    font-weight: 600;
}
QPushButton:hover {
    border-color: #38bdf8;
    background: #1e293b;
}
QPushButton:pressed {
    background: #334155;
}
QPushButton:disabled {
    color: #475569;
    background: #020617;
    border-color: #0f172a;
}
QComboBox,
QLineEdit,
QSpinBox,
QTextEdit {
    background: #020617;
    color: #f8fafc;
    border: 1px solid #1e293b;
    border-radius: 8px;
    min-height: 28px;
    padding: 5px 10px;
    selection-background-color: #065f46;
}
QTextEdit {
    min-height: 70px;
}
QComboBox:focus,
QLineEdit:focus,
QSpinBox:focus,
QTextEdit:focus {
    border: 1.5px solid #10b981;
    background: #0f172a;
}
QComboBox::drop-down {
    border: 0px;
    width: 20px;
}
QComboBox QAbstractItemView {
    background-color: #0f172a;
    color: #f8fafc;
    border: 1px solid #1e293b;
    selection-background-color: #065f46;
    selection-color: #ffffff;
}
QCheckBox {
    color: #f8fafc;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #334155;
    background: #020617;
}
QCheckBox::indicator:checked {
    background: #10b981;
    border-color: #10b981;
}
"""
