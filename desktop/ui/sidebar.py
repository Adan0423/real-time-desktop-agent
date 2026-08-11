from __future__ import annotations

from rtda.capture.interface import CaptureConfig, MonitorInfo

from desktop.ui.ai_panel import AiPanel
from desktop.ui.runtime_panel import RuntimePanel
from desktop.ui.target_panel import TargetPanel
from desktop.ui.widgets import StatusPill, make_label


class ControlSidebar:
    """Compact left rail for local desktop testing of the RTDA complement."""

    def __init__(
        self,
        *,
        config: CaptureConfig,
        enable_perception_tools: bool,
        show_capture_overlay: bool = True,
    ) -> None:
        from PySide6.QtWidgets import QFrame, QTabWidget, QVBoxLayout

        self.status = StatusPill("Extension local lista")
        self.target = TargetPanel(
            config=config,
            enable_perception_tools=enable_perception_tools,
            show_capture_overlay=show_capture_overlay,
        )
        self.runtime = RuntimePanel(enable_perception_tools=enable_perception_tools)
        self.ai = AiPanel()

        tabs = QTabWidget()
        tabs.setObjectName("modeTabs")
        tabs.addTab(self._capture_tab(), "Captura")
        tabs.addTab(self.ai.widget, "IA")

        layout = QVBoxLayout()
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        layout.addWidget(make_label("RTDA Desktop", "appTitle"))
        layout.addWidget(make_label("Control local del complemento IA", "mutedText"))
        layout.addWidget(self.status.widget)
        layout.addWidget(tabs, 1)

        self.widget = QFrame()
        self.widget.setObjectName("sidebar")
        self.widget.setMinimumWidth(308)
        self.widget.setMaximumWidth(330)
        self.widget.setLayout(layout)

    def set_monitors(self, monitors: list[MonitorInfo]) -> None:
        self.target.set_monitors(monitors)

    def set_status(self, *, running: bool, paused: bool) -> None:
        if running and paused:
            self.status.set("Extension pausada", "paused")
            return
        if running:
            self.status.set("Extension activa", "active")
            return
        self.status.set("Extension local lista", "idle")

    def _capture_tab(self):
        from PySide6.QtWidgets import QVBoxLayout, QWidget

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self.target.widget)
        layout.addWidget(self.runtime.widget)
        layout.addStretch(1)

        tab = QWidget()
        tab.setLayout(layout)
        return tab
