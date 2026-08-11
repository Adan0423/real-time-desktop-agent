from __future__ import annotations

from dataclasses import dataclass

from rtda.capture.interface import CaptureConfig, MonitorInfo
from rtda.capture.region import Region

from desktop.ui.widgets import SectionPanel, coord_spin, make_label


@dataclass(frozen=True, slots=True)
class TargetSelection:
    backend: str
    target_fps: int
    monitor_index: int
    window_title: str | None
    region: Region | None
    show_border: bool


class TargetPanel:
    """Capture target controls for monitor, backend, window and region."""

    def __init__(
        self,
        *,
        config: CaptureConfig,
        enable_perception_tools: bool,
        show_capture_overlay: bool,
    ) -> None:
        from PySide6.QtWidgets import QCheckBox, QComboBox, QGridLayout, QHBoxLayout, QLineEdit, QSpinBox

        self.monitor_combo = QComboBox()
        self.backend_combo = QComboBox()
        self.backend_combo.addItems(["dxgi", "wgc"])
        self.backend_combo.setCurrentText(config.backend)
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 240)
        self.fps_spin.setValue(config.target_fps)
        self.window_title = QLineEdit()
        self.window_title.setPlaceholderText("Titulo de ventana para WGC")
        self.region_enabled = QCheckBox("Region")
        self.overlay_enabled = QCheckBox("Marco verde")
        self.overlay_enabled.setChecked(show_capture_overlay)
        self.change_detection_enabled = QCheckBox("Cambios")
        self.change_detection_enabled.setChecked(False)
        self.left_spin = coord_spin(config.region.left if config.region else 0)
        self.top_spin = coord_spin(config.region.top if config.region else 0)
        self.right_spin = coord_spin(config.region.right if config.region else 3840)
        self.bottom_spin = coord_spin(config.region.bottom if config.region else 2160)
        self.region_enabled.setChecked(config.region is not None)
        self.region_enabled.toggled.connect(self._set_region_controls_enabled)

        fields = QGridLayout()
        fields.setHorizontalSpacing(8)
        fields.setVerticalSpacing(7)
        for row, (label, widget) in enumerate(
            (
                ("Monitor", self.monitor_combo),
                ("Backend", self.backend_combo),
                ("FPS", self.fps_spin),
                ("Ventana", self.window_title),
            )
        ):
            fields.addWidget(make_label(label, "fieldLabel"), row, 0)
            fields.addWidget(widget, row, 1)

        toggles = QHBoxLayout()
        toggles.setContentsMargins(0, 0, 0, 0)
        toggles.setSpacing(10)
        toggles.addWidget(self.region_enabled)
        toggles.addWidget(self.overlay_enabled)
        if enable_perception_tools:
            toggles.addWidget(self.change_detection_enabled)
        toggles.addStretch(1)
        fields.addLayout(toggles, 4, 0, 1, 2)

        region = QGridLayout()
        region.setHorizontalSpacing(6)
        region.setVerticalSpacing(6)
        for idx, (label, widget) in enumerate(
            (
                ("L", self.left_spin),
                ("T", self.top_spin),
                ("R", self.right_spin),
                ("B", self.bottom_spin),
            )
        ):
            region.addWidget(make_label(label, "fieldLabel"), idx // 2, (idx % 2) * 2)
            region.addWidget(widget, idx // 2, (idx % 2) * 2 + 1)
        fields.addLayout(region, 5, 0, 1, 2)

        self.widget = SectionPanel("Objetivo", fields).widget
        self._set_region_controls_enabled(self.region_enabled.isChecked())

    def set_monitors(self, monitors: list[MonitorInfo]) -> None:
        self.monitor_combo.clear()
        if not monitors:
            self.monitor_combo.addItem("0: monitor principal")
            return
        for monitor in monitors:
            self.monitor_combo.addItem(monitor.label)

    def selection(self) -> TargetSelection:
        region = None
        if self.region_enabled.isChecked():
            region = Region(
                self.left_spin.value(),
                self.top_spin.value(),
                self.right_spin.value(),
                self.bottom_spin.value(),
            )
        window_title = self.window_title.text().strip() or None
        backend = "wgc" if window_title else self.backend_combo.currentText()
        if window_title:
            self.backend_combo.setCurrentText("wgc")
        return TargetSelection(
            backend=backend,
            target_fps=self.fps_spin.value(),
            monitor_index=max(0, self.monitor_combo.currentIndex()),
            window_title=window_title,
            region=region,
            show_border=self.overlay_enabled.isChecked(),
        )

    def _set_region_controls_enabled(self, enabled: bool) -> None:
        for widget in (self.left_spin, self.top_spin, self.right_spin, self.bottom_spin):
            widget.setEnabled(enabled)
