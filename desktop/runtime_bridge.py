from __future__ import annotations

import time
from dataclasses import replace
from typing import Any

from rtda.capture.interface import CaptureConfig, CaptureStats, MonitorInfo
from rtda.capture.region import Region
from rtda.complement import RTDAComplementConfig, RTDAComplementRuntime
from rtda.overlay.geometry import capture_rect_from_config
from rtda.overlay.qt import GreenCaptureOverlay


class DesktopRuntimeBridge:
    """Small desktop-facing wrapper around the RTDA IA complement runtime."""

    def __init__(self, config: CaptureConfig, *, enable_perception_tools: bool) -> None:
        self.runtime = RTDAComplementRuntime(config)
        self._overlay = GreenCaptureOverlay()
        self._last_overlay_update = 0.0
        self._enable_perception_tools = enable_perception_tools
        self._change_processor: Any | None = None
        self._uia_inspector: Any | None = None
        self._latest_change: Any | None = None
        self.reset_perception_tools()

    @property
    def running(self) -> bool:
        return self.runtime.running

    @property
    def paused(self) -> bool:
        return self.runtime.paused

    @property
    def config(self) -> CaptureConfig:
        return self.runtime.config

    @property
    def latest_change(self) -> Any | None:
        return self._latest_change

    def list_monitors(self) -> list[MonitorInfo]:
        return self.runtime.list_monitors()

    def start(
        self,
        *,
        base_config: CaptureConfig,
        backend: str,
        target_fps: int,
        monitor_index: int,
        window_title: str | None,
        region: Region | None,
        show_border: bool,
    ) -> None:
        if window_title:
            backend = "wgc"
        config = replace(
            base_config,
            backend=backend,
            target_fps=target_fps,
            monitor_index=max(0, monitor_index),
            region=region,
            window_title=window_title,
        )
        settings = RTDAComplementConfig(capture=config, enable_border=False)
        self.runtime.start_capture(settings)
        self.reset_perception_tools()
        self.refresh_overlay(show_border)

    def stop(self) -> None:
        self.runtime.stop_capture()
        self._overlay.hide()

    def pause_or_resume(self) -> None:
        if not self.running:
            return
        if self.paused:
            self.runtime.resume_capture()
        else:
            self.runtime.pause_capture()

    def metrics(self) -> CaptureStats:
        return self.runtime.metrics()

    def latest_frame(self):
        return self.runtime.latest_frame()

    def process_change_detection(self, enabled: bool) -> Any | None:
        if not enabled or self._change_processor is None:
            return self._latest_change
        result = self._change_processor.process_buffer(self.runtime.buffer)
        self._latest_change = result or self._latest_change
        return self._latest_change

    def inspect_uia(self, *, window_title: str | None) -> str | None:
        if not self._enable_perception_tools or self._uia_inspector is None:
            return None
        snapshot = self._uia_inspector.snapshot(window_title=window_title)
        if self._change_processor is not None:
            self._change_processor.metrics.record_uia_snapshot(
                timestamp=time.perf_counter(),
                uia_latency_ms=snapshot.latency_ms,
                element_count=snapshot.element_count,
            )
        error_text = f", errores: {len(snapshot.errors)}" if snapshot.errors else ""
        target = f" ({window_title})" if window_title else ""
        return f"UIA{target}: {snapshot.element_count} elementos, {snapshot.latency_ms:.1f} ms{error_text}"

    def refresh_overlay(self, enabled: bool, *, throttle_s: float = 0.0) -> None:
        if not enabled or not self.running:
            self._overlay.hide()
            return
        now = time.perf_counter()
        if throttle_s and now - self._last_overlay_update < throttle_s:
            return
        self._last_overlay_update = now
        rect = capture_rect_from_config(self.runtime.config, self.runtime.list_monitors())
        self._overlay.show_rect(rect)

    def reset_perception_tools(self) -> None:
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

    def shutdown(self) -> None:
        self.stop()
