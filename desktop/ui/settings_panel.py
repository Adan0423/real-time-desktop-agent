from __future__ import annotations

from desktop.ui.widgets import SectionPanel


class SettingsPanel:
    """Desktop-only runtime preferences kept away from the capture page."""

    def __init__(
        self,
        *,
        enable_perception_tools: bool,
        show_capture_overlay: bool,
        show_floating_control: bool,
    ) -> None:
        from PySide6.QtWidgets import QCheckBox, QVBoxLayout

        self.border_enabled = QCheckBox("🟩 Mostrar marco verde de captura")
        self.border_enabled.setChecked(show_capture_overlay)
        self.change_detection_enabled = QCheckBox("🔍 Activar detección de cambios por ROI")
        self.change_detection_enabled.setChecked(False)
        self.change_detection_enabled.setEnabled(enable_perception_tools)
        self.floating_enabled = QCheckBox("🗔 Panel flotante en primer plano")
        self.floating_enabled.setChecked(show_floating_control)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self.border_enabled)
        layout.addWidget(self.change_detection_enabled)
        layout.addWidget(self.floating_enabled)
        layout.addStretch(1)

        self.widget = SectionPanel("⚙️ Configuración Preferida", layout).widget


    def show_border(self) -> bool:
        return self.border_enabled.isChecked()

    def detect_changes(self) -> bool:
        return self.change_detection_enabled.isChecked()
