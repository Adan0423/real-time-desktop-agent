"""Capture primitives for RTDA."""

from rtda.capture.frame import Frame
from rtda.capture.frame_buffer import FrameBuffer
from rtda.capture.interface import CaptureConfig, CaptureStats, MonitorInfo, ScreenCapture
from rtda.capture.region import Region
from rtda.capture.diagnostics import CaptureDiagnosticResult, run_capture_diagnostic

__all__ = [
    "CaptureConfig",
    "CaptureDiagnosticResult",
    "CaptureStats",
    "Frame",
    "FrameBuffer",
    "MonitorInfo",
    "Region",
    "ScreenCapture",
    "run_capture_diagnostic",
]
