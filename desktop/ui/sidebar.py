from __future__ import annotations

from rtda.capture.interface import CaptureConfig, MonitorInfo

from desktop.ui.ai_panel import AiPanel
from desktop.ui.runtime_panel import ActionBar, RuntimePanel
from desktop.ui.settings_panel import SettingsPanel
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
        show_floating_control: bool = True,
    ) -> None:
        from PySide6.QtWidgets import QFrame, QHBoxLayout, QPushButton, QStackedWidget, QVBoxLayout

        self.status = StatusPill("Extension local lista")
        self.target = TargetPanel(config=config)
        self.runtime = RuntimePanel(enable_perception_tools=enable_perception_tools)
        self.ai = AiPanel()
        self.settings = SettingsPanel(
            enable_perception_tools=enable_perception_tools,
            show_capture_overlay=show_capture_overlay,
            show_floating_control=show_floating_control,
        )
        self.actions = ActionBar(enable_perception_tools=enable_perception_tools)

        self.pages = QStackedWidget()
        self.pages.setObjectName("pageStack")
        self.pages.addWidget(self._page(self.target.widget))
        self.pages.addWidget(self._page(self.runtime.widget))
        self.pages.addWidget(self.ai.widget)
        self.pages.addWidget(self._page(self.settings.widget))

        nav = QHBoxLayout()
        nav.setContentsMargins(0, 0, 0, 0)
        nav.setSpacing(4)
        self.page_buttons: dict[str, QPushButton] = {}
        for index, (key, label) in enumerate(
            (
                ("capture", "📷 Captura"),
                ("metrics", "📊 Métricas"),
                ("ai", "🧠 IA"),
                ("settings", "⚙️ Config"),
            )
        ):
            button = QPushButton(label)
            button.setObjectName("navButton")
            button.setCheckable(True)
            button.clicked.connect(lambda _checked=False, page=index: self.set_page(page))
            nav.addWidget(button)
            self.page_buttons[key] = button
        self.set_page(0)

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        layout.addWidget(make_label("🌟 RTDA", "appTitle"))
        layout.addWidget(make_label("🔌 Desktop Agent OS", "mutedText"))
        layout.addWidget(self.status.widget)
        layout.addLayout(nav)
        layout.addWidget(self.pages, 1)
        layout.addWidget(self.actions.widget)


        self.widget = QFrame()
        self.widget.setObjectName("sidebar")
        self.widget.setMinimumWidth(292)
        self.widget.setMaximumWidth(310)
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

    def set_page(self, index: int) -> None:
        self.pages.setCurrentIndex(index)
        for button_index, button in enumerate(self.page_buttons.values()):
            button.setChecked(button_index == index)

    def _page(self, child):
        from PySide6.QtWidgets import QVBoxLayout, QWidget

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(child)
        layout.addStretch(1)

        page = QWidget()
        page.setLayout(layout)
        return page
