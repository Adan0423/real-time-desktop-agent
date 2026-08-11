from __future__ import annotations

import time
from dataclasses import replace
from typing import Any

from rtda.capture.interface import CaptureConfig
from rtda.capture.region import Region
from rtda.capture.windows_capture import WindowsCaptureEngine


class CaptureDashboard:
    def __init__(
        self,
        config: CaptureConfig | None = None,
        *,
        enable_perception_tools: bool = False,
    ) -> None:
        try:
            from PySide6.QtCore import Qt, QTimer
            from PySide6.QtGui import QImage, QPainter, QPen, QPixmap
            from PySide6.QtWidgets import (
                QCheckBox,
                QComboBox,
                QFormLayout,
                QHBoxLayout,
                QLabel,
                QLineEdit,
                QPushButton,
                QSpinBox,
                QVBoxLayout,
                QWidget,
            )
        except ImportError as exc:
            raise RuntimeError(
                "Missing optional dependency 'PySide6'. "
                "Install with: python -m pip install -e .[gui]"
            ) from exc

        self.Qt = Qt
        self.QImage = QImage
        self.QPainter = QPainter
        self.QPen = QPen
        self.QPixmap = QPixmap
        self.QTimer = QTimer
        self.QWidget = QWidget

        self._config = config or CaptureConfig()
        self._enable_perception_tools = enable_perception_tools
        self._capture = WindowsCaptureEngine(self._config)
        self._change_processor: Any | None = None
        self._uia_inspector: Any | None = None
        self._latest_change: Any | None = None
        self._reset_perception_tools()

        self.widget = QWidget()
        self.widget.setWindowTitle("RTDA Capture Engine")
        self.widget.resize(1120, 760)

        self.monitor_combo = QComboBox()
        self.backend_combo = QComboBox()
        self.backend_combo.addItems(["dxgi", "wgc"])
        self.backend_combo.setCurrentText(self._config.backend)
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 240)
        self.fps_spin.setValue(self._config.target_fps)
        self.window_title = QLineEdit()
        self.window_title.setPlaceholderText("Window title for WGC")
        self.region_enabled = QCheckBox()
        self.change_detection_enabled = QCheckBox()
        self.change_detection_enabled.setChecked(False)
        self.left_spin = self._coord_spin()
        self.top_spin = self._coord_spin()
        self.right_spin = self._coord_spin(3840)
        self.bottom_spin = self._coord_spin(2160)

        self.start_button = QPushButton("Start")
        self.pause_button = QPushButton("Pause")
        self.stop_button = QPushButton("Stop")
        self.uia_button = QPushButton("Inspect UIA")
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.uia_button.setEnabled(self._enable_perception_tools)

        self.metrics_label = QLabel("Capture FPS: 0.0\nResolution: -\nLatency: -\nDropped: 0")
        self.uia_label = QLabel("UIA: not inspected")
        self.preview_label = QLabel("No frame")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(800, 520)
        self.preview_label.setStyleSheet("background:#111; color:#ddd; border:1px solid #333;")

        form = QFormLayout()
        form.addRow("Monitor", self.monitor_combo)
        form.addRow("Backend", self.backend_combo)
        form.addRow("Target FPS", self.fps_spin)
        form.addRow("Window", self.window_title)
        form.addRow("Use region", self.region_enabled)
        if self._enable_perception_tools:
            form.addRow("Change detect", self.change_detection_enabled)
        form.addRow("Left", self.left_spin)
        form.addRow("Top", self.top_spin)
        form.addRow("Right", self.right_spin)
        form.addRow("Bottom", self.bottom_spin)

        buttons = QHBoxLayout()
        buttons.addWidget(self.start_button)
        buttons.addWidget(self.pause_button)
        buttons.addWidget(self.stop_button)
        if self._enable_perception_tools:
            buttons.addWidget(self.uia_button)

        side = QVBoxLayout()
        side.addLayout(form)
        side.addLayout(buttons)
        side.addWidget(self.metrics_label)
        if self._enable_perception_tools:
            side.addWidget(self.uia_label)
        side.addStretch(1)

        root = QHBoxLayout()
        root.addLayout(side, 0)
        root.addWidget(self.preview_label, 1)
        self.widget.setLayout(root)

        self.timer = QTimer()
        self.timer.setInterval(33)
        self.timer.timeout.connect(self._update_preview)

        self.start_button.clicked.connect(self.start)
        self.pause_button.clicked.connect(self.pause_or_resume)
        self.stop_button.clicked.connect(self.stop)
        self.uia_button.clicked.connect(self.inspect_uia)

        self._load_monitors()

    def show(self) -> None:
        self.widget.show()

    def start(self) -> None:
        self.stop()
        region = None
        if self.region_enabled.isChecked():
            region = Region(
                self.left_spin.value(),
                self.top_spin.value(),
                self.right_spin.value(),
                self.bottom_spin.value(),
            )
        window_title = self.window_title.text().strip() or None
        backend = self.backend_combo.currentText()
        if window_title:
            backend = "wgc"
            self.backend_combo.setCurrentText("wgc")
        config = replace(
            self._config,
            backend=backend,
            target_fps=self.fps_spin.value(),
            monitor_index=max(0, self.monitor_combo.currentIndex()),
            region=region,
            window_title=window_title,
        )
        self._capture = WindowsCaptureEngine(config)
        self._reset_perception_tools()
        self._capture.start()
        self.timer.start()
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.stop_button.setEnabled(True)

    def stop(self) -> None:
        self.timer.stop()
        self._capture.stop()
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.pause_button.setText("Pause")

    def pause_or_resume(self) -> None:
        if self.pause_button.text() == "Pause":
            self._capture.pause()
            self.pause_button.setText("Resume")
        else:
            self._capture.resume()
            self.pause_button.setText("Pause")

    def inspect_uia(self) -> None:
        if not self._enable_perception_tools:
            return
        if self._uia_inspector is None:
            self._reset_perception_tools()
        if self._uia_inspector is None:
            return
        window_title = self.window_title.text().strip() or None
        snapshot = self._uia_inspector.snapshot(window_title=window_title)
        if self._change_processor is not None:
            self._change_processor.metrics.record_uia_snapshot(
                timestamp=time.perf_counter(),
                uia_latency_ms=snapshot.latency_ms,
                element_count=snapshot.element_count,
            )
        error_text = f", errors: {len(snapshot.errors)}" if snapshot.errors else ""
        target = f" ({window_title})" if window_title else ""
        self.uia_label.setText(
            f"UIA{target}: {snapshot.element_count} elements, "
            f"{snapshot.latency_ms:.1f} ms{error_text}"
        )

    def _load_monitors(self) -> None:
        self.monitor_combo.clear()
        monitors = self._capture.list_monitors()
        if not monitors:
            self.monitor_combo.addItem("0: primary monitor")
            return
        for monitor in monitors:
            self.monitor_combo.addItem(monitor.label)

    def _update_preview(self) -> None:
        frame = self._capture.latest_frame()
        stats = self._capture.metrics()
        change_enabled = (
            self._enable_perception_tools
            and self.change_detection_enabled.isChecked()
            and self._change_processor is not None
        )
        if change_enabled:
            result = self._change_processor.process_buffer(self._capture.buffer)
            self._latest_change = result or self._latest_change
        resolution = "-"
        if stats.latest_width and stats.latest_height:
            resolution = f"{stats.latest_width}x{stats.latest_height}"
        latency = "-" if stats.capture_latency_ms is None else f"{stats.capture_latency_ms:.2f} ms"
        metric_lines = [
            f"Capture FPS: {stats.capture_fps:.1f}",
            f"Resolution: {resolution}",
            f"Latency: {latency}",
            f"Dropped: {stats.buffer_dropped_frames}",
            f"Missed est.: {stats.estimated_missed_frames}",
            f"Frames: {stats.frames_captured}",
            f"Errors: {stats.backend_errors}",
        ]
        if self._enable_perception_tools and self._change_processor is not None:
            processing_stats = self._change_processor.metrics.snapshot()
            metric_lines.extend(
                [
                    f"Processing FPS: {processing_stats.processing_fps:.1f}",
                    f"OpenCV Latency: {self._format_ms(processing_stats.opencv_latency_ms)}",
                    f"Changed regions: {processing_stats.latest_changed_regions}",
                    f"Changed ratio: {processing_stats.latest_changed_ratio:.4f}",
                ]
            )
        self.metrics_label.setText(
            "\n".join(metric_lines)
        )
        if frame is None:
            return
        data = frame.data
        if data.shape[2] == 4:
            image_format = self.QImage.Format.Format_BGRA8888
            bytes_per_line = data.strides[0]
            image = self.QImage(data.data, frame.width, frame.height, bytes_per_line, image_format).copy()
        else:
            image_format = self.QImage.Format.Format_RGB888
            bytes_per_line = data.strides[0]
            image = self.QImage(data.data, frame.width, frame.height, bytes_per_line, image_format).copy()
        pixmap = self.QPixmap.fromImage(image)
        if change_enabled and self._latest_change is not None:
            pixmap = self._draw_change_regions(pixmap, self._latest_change)
        scaled = pixmap.scaled(
            self.preview_label.size(),
            self.Qt.AspectRatioMode.KeepAspectRatio,
            self.Qt.TransformationMode.SmoothTransformation,
        )
        self.preview_label.setPixmap(scaled)

    @staticmethod
    def _coord_spin(default: int = 0):
        from PySide6.QtWidgets import QSpinBox

        spin = QSpinBox()
        spin.setRange(0, 16384)
        spin.setValue(default)
        return spin

    @staticmethod
    def _format_ms(value: float | None) -> str:
        return "-" if value is None else f"{value:.2f} ms"

    def _reset_perception_tools(self) -> None:
        self._latest_change = None
        self._change_processor = None
        self._uia_inspector = None
        if not self._enable_perception_tools:
            return

        from rtda.perception.change_detector import FrameChangeProcessor
        from rtda.perception.opencv_detector import OpenCVChangeDetector
        from rtda.perception.uia import UIAConfig, WindowsUIAutomationInspector

        self._change_processor = FrameChangeProcessor(OpenCVChangeDetector())
        self._uia_inspector = WindowsUIAutomationInspector(UIAConfig(max_depth=3, max_elements=120))

    def _draw_change_regions(self, pixmap, result: Any):
        if not result.regions:
            return pixmap
        overlay = pixmap.copy()
        painter = self.QPainter(overlay)
        pen = self.QPen(self.Qt.GlobalColor.red)
        pen.setWidth(2)
        painter.setPen(pen)
        for region in result.regions:
            bbox = region.bbox
            painter.drawRect(bbox.left, bbox.top, bbox.width, bbox.height)
        painter.end()
        return overlay
