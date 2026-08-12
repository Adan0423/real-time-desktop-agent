from __future__ import annotations

from dataclasses import dataclass, field, replace

from rtda.actions.engine import ActionEngine
from rtda.actions.pyautogui_executor import PyAutoGUIActionExecutor
from rtda.capture.frame import Frame
from rtda.capture.frame_buffer import FrameBuffer
from rtda.capture.interface import CaptureConfig, CaptureStats, MonitorInfo
from rtda.capture.windows_capture import WindowsCaptureEngine
from rtda.models.actions import ActionCommand, ActionResult, ActionType
from rtda.models.perception import BoundingBox, ChangeDetectionResult, PerceptionElement, UIASnapshot
from rtda.overlay.geometry import OverlayRect, capture_rect_from_config
from rtda.perception.change_detector import FrameChangeProcessor
from rtda.perception.opencv_detector import OpenCVChangeDetector
from rtda.perception.uia import UIAConfig, WindowsUIAutomationInspector


@dataclass(slots=True)
class RTDAComplementConfig:
    """Configuration for the reusable RTDA IA complement runtime."""

    capture: CaptureConfig = field(default_factory=CaptureConfig)
    dry_run_actions: bool = True
    enable_border: bool = False
    uia_max_depth: int = 3
    uia_max_elements: int = 120


@dataclass(frozen=True, slots=True)
class RTDAObservation:
    """Single realtime observation produced by the complement boundary."""

    frame: Frame | None
    metrics: CaptureStats
    change: ChangeDetectionResult | None = None
    ui_snapshot: UIASnapshot | None = None
    border_rect: OverlayRect | None = None


class RTDAComplementRuntime:
    """Stable in-process runtime for IA hosts and local control surfaces.

    This class is the main developer-facing boundary for the project. It owns
    realtime capture, frame buffering, vision/change detection, UIA snapshots,
    mouse/keyboard actions and the optional green border overlay. The desktop
    app and MCP layer should consume this boundary instead of reaching into UI
    internals.
    """

    def __init__(
        self,
        config: CaptureConfig | RTDAComplementConfig | None = None,
        *,
        action_engine: ActionEngine | None = None,
        change_processor: FrameChangeProcessor | None = None,
        uia_inspector: WindowsUIAutomationInspector | None = None,
    ) -> None:
        self._settings = self._normalize_config(config)
        self._config = self._settings.capture
        self._capture = WindowsCaptureEngine(self._config)
        self._action_engine = action_engine or self._build_action_engine()
        self._change_processor = change_processor or FrameChangeProcessor(OpenCVChangeDetector())
        self._uia_inspector = uia_inspector or WindowsUIAutomationInspector(
            UIAConfig(max_depth=self._settings.uia_max_depth, max_elements=self._settings.uia_max_elements)
        )
        self._border_overlay = None
        self._running = False
        self._paused = False

    @property
    def settings(self) -> RTDAComplementConfig:
        return self._settings

    @property
    def config(self) -> CaptureConfig:
        return self._config

    @property
    def buffer(self) -> FrameBuffer:
        return self._capture.buffer

    @property
    def action_engine(self) -> ActionEngine:
        return self._action_engine

    @property
    def running(self) -> bool:
        return self._running

    @property
    def paused(self) -> bool:
        return self._paused

    def capabilities(self) -> dict[str, bool]:
        return {
            "realtime_capture": True,
            "frame_buffer": True,
            "mouse": True,
            "keyboard": True,
            "vision": True,
            "uia": True,
            "green_border": True,
            "safe_actions": True,
        }

    def list_monitors(self) -> list[MonitorInfo]:
        return self._capture.list_monitors()

    def start(self) -> None:
        self.start_capture()

    def stop(self) -> None:
        self.stop_capture()

    def pause(self) -> None:
        self.pause_capture()

    def resume(self) -> None:
        self.resume_capture()

    def get_fps(self) -> float:
        return self.metrics().capture_fps

    def get_latency(self) -> float | None:
        return self.metrics().capture_latency_ms

    def start_capture(self, config: CaptureConfig | RTDAComplementConfig | None = None) -> None:
        self.stop_capture()
        if config is not None:
            self._settings = self._merge_config(config)
            self._config = self._settings.capture
            self._action_engine = self._build_action_engine()
            self._uia_inspector = WindowsUIAutomationInspector(
                UIAConfig(max_depth=self._settings.uia_max_depth, max_elements=self._settings.uia_max_elements)
            )
        self._capture = WindowsCaptureEngine(self._config)
        self._capture.start()
        self._running = True
        self._paused = False
        self.refresh_border()

    def stop_capture(self) -> None:
        self._capture.stop()
        self.buffer.clear()
        self.hide_border()
        self._running = False
        self._paused = False

    def pause_capture(self) -> None:
        if not self._running:
            return
        self._capture.pause()
        self._paused = True

    def resume_capture(self) -> None:
        if not self._running:
            return
        self._capture.resume()
        self._paused = False

    def latest_frame(self) -> Frame | None:
        return self._capture.latest_frame()

    def metrics(self) -> CaptureStats:
        return self._capture.metrics()

    def observe(
        self,
        *,
        include_changes: bool = True,
        include_uia: bool = False,
        window_title: str | None = None,
        refresh_border: bool = True,
    ) -> RTDAObservation:
        change = self.detect_changes() if include_changes else None
        ui_snapshot = self.inspect_ui(window_title=window_title) if include_uia else None
        border_rect = self.refresh_border() if refresh_border else self.capture_rect()
        return RTDAObservation(
            frame=self.latest_frame(),
            metrics=self.metrics(),
            change=change,
            ui_snapshot=ui_snapshot,
            border_rect=border_rect,
        )

    def detect_changes(self) -> ChangeDetectionResult | None:
        return self._change_processor.process_buffer(self.buffer)

    def inspect_ui(self, *, window_title: str | None = None) -> UIASnapshot:
        snapshot = self._uia_inspector.snapshot(window_title=window_title)
        self.update_perception_elements(snapshot.to_perception_elements())
        return snapshot

    def update_perception_elements(self, elements: tuple[PerceptionElement, ...]) -> None:
        self._action_engine.resolver.update(elements)

    def execute_action(self, command: ActionCommand) -> ActionResult:
        return self._action_engine.execute(command)

    def click(self, target: str | None = None, *, bbox: BoundingBox | None = None) -> ActionResult:
        return self.execute_action(ActionCommand(action=ActionType.CLICK, target=target, bbox=bbox))

    def move(self, target: str | None = None, *, bbox: BoundingBox | None = None) -> ActionResult:
        return self.execute_action(ActionCommand(action=ActionType.MOVE, target=target, bbox=bbox))

    def type_text(self, value: str, *, target: str | None = None, bbox: BoundingBox | None = None) -> ActionResult:
        return self.execute_action(ActionCommand(action=ActionType.TYPE, target=target, value=value, bbox=bbox))

    def press(self, key: str) -> ActionResult:
        return self.execute_action(ActionCommand(action=ActionType.PRESS, value=key))

    def hotkey(self, *keys: str) -> ActionResult:
        return self.execute_action(ActionCommand(action=ActionType.HOTKEY, keys=list(keys)))

    def scroll(self, amount: int) -> ActionResult:
        return self.execute_action(ActionCommand(action=ActionType.SCROLL, amount=amount))

    def capture_rect(self) -> OverlayRect | None:
        return capture_rect_from_config(self._config, self.list_monitors())

    def refresh_border(self) -> OverlayRect | None:
        if not self._settings.enable_border or not self._running:
            self.hide_border()
            return None
        rect = self.capture_rect()
        if rect is None:
            self.hide_border()
            return None
        overlay = self._ensure_border_overlay()
        overlay.show_rect(rect)
        return rect

    def hide_border(self) -> None:
        if self._border_overlay is not None:
            self._border_overlay.hide()

    def _build_action_engine(self) -> ActionEngine:
        return ActionEngine(executor=PyAutoGUIActionExecutor(dry_run=self._settings.dry_run_actions))

    def _ensure_border_overlay(self):
        if self._border_overlay is None:
            self._border_overlay = self._create_border_overlay()
        return self._border_overlay

    @staticmethod
    def _create_border_overlay():
        from PySide6.QtWidgets import QApplication

        if QApplication.instance() is None:
            QApplication([])
        from rtda.overlay.qt import GreenCaptureOverlay

        return GreenCaptureOverlay()

    @staticmethod
    def _normalize_config(config: CaptureConfig | RTDAComplementConfig | None) -> RTDAComplementConfig:
        if config is None:
            return RTDAComplementConfig()
        if isinstance(config, RTDAComplementConfig):
            return config
        return RTDAComplementConfig(capture=config)

    def _merge_config(self, config: CaptureConfig | RTDAComplementConfig) -> RTDAComplementConfig:
        if isinstance(config, RTDAComplementConfig):
            return config
        return replace(self._settings, capture=config)
