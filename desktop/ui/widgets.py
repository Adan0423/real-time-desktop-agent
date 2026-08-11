from __future__ import annotations


def make_label(text: str, object_name: str):
    from PySide6.QtWidgets import QLabel

    label = QLabel(text)
    label.setObjectName(object_name)
    return label


def coord_spin(default: int = 0):
    from PySide6.QtWidgets import QSpinBox

    spin = QSpinBox()
    spin.setRange(0, 16384)
    spin.setValue(default)
    return spin


class StatusPill:
    """Compact status label with tone-aware styling."""

    def __init__(self, text: str) -> None:
        from PySide6.QtWidgets import QLabel

        self.widget = QLabel(text)
        self.widget.setObjectName("statusPill")
        self.set_tone("idle")

    def set(self, text: str, tone: str) -> None:
        self.widget.setText(text)
        self.set_tone(tone)

    def set_tone(self, tone: str) -> None:
        self.widget.setProperty("tone", tone)
        self.widget.style().unpolish(self.widget)
        self.widget.style().polish(self.widget)


class SectionPanel:
    """Bordered group used by the dashboard sidebar."""

    def __init__(self, title: str, content_layout) -> None:
        from PySide6.QtWidgets import QFrame, QVBoxLayout

        label = make_label(title, "sectionTitle")
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(9)
        layout.addWidget(label)
        layout.addLayout(content_layout)

        self.widget = QFrame()
        self.widget.setObjectName("sectionPanel")
        self.widget.setLayout(layout)


class MetricTile:
    """Small metric tile whose value can be updated from runtime stats."""

    def __init__(self, label: str, value: str = "-") -> None:
        from PySide6.QtWidgets import QFrame, QVBoxLayout

        self.value = make_label(value, "metricValue")
        label_widget = make_label(label, "metricLabel")
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 7, 10, 8)
        layout.setSpacing(2)
        layout.addWidget(label_widget)
        layout.addWidget(self.value)

        self.widget = QFrame()
        self.widget.setObjectName("metricTile")
        self.widget.setLayout(layout)

    def set_text(self, text: str) -> None:
        self.value.setText(text)
