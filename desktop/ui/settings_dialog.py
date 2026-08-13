from __future__ import annotations

from desktop.ui.settings_panel import SettingsPanel
from desktop.ui.widgets import make_label


class SettingsDialog:
    """Modal settings dialog for RTDA Desktop configuration."""

    def __init__(
        self,
        parent,
        *,
        enable_perception_tools: bool,
        show_capture_overlay: bool = True,
        show_floating_control: bool = True,
    ) -> None:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QDialog, QHBoxLayout, QPushButton, QVBoxLayout

        self.panel = SettingsPanel(
            enable_perception_tools=enable_perception_tools,
            show_capture_overlay=show_capture_overlay,
            show_floating_control=show_floating_control,
        )

        self.dialog = QDialog(parent)
        self.dialog.setObjectName("settingsDialog")
        self.dialog.setWindowTitle("⚙️ Ajustes y Configuración - RTDA")
        self.dialog.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.dialog.resize(360, 280)

        close_button = QPushButton("Aceptar")
        close_button.clicked.connect(self.dialog.accept)

        bottom = QHBoxLayout()
        bottom.addStretch(1)
        bottom.addWidget(close_button)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addWidget(make_label("⚙️ Configuración del Sistema", "appTitle"))
        layout.addWidget(self.panel.widget)
        layout.addLayout(bottom)

        self.dialog.setLayout(layout)

    def exec(self) -> int:
        return self.dialog.exec()
