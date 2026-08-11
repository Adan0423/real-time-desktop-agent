from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any

from rtda.capture.interface import CaptureConfig, CaptureStats, MonitorInfo, ScreenCapture


@dataclass(frozen=True, slots=True)
class CaptureDiagnosticResult:
    config: CaptureConfig
    monitors: tuple[MonitorInfo, ...]
    checks: dict[str, bool]
    metrics: CaptureStats
    latest_frame: dict[str, Any] | None
    errors: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        required = (
            "monitors_detected",
            "capture_started",
            "frames_received",
            "latest_frame_available",
            "resolution_reported",
            "latency_reported",
            "backend_errors_zero",
            "pause_resume_called",
            "stopped_cleanly",
        )
        return all(self.checks.get(name, False) for name in required)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["passed"] = self.passed
        return payload


def monitors_to_dict(monitors: list[MonitorInfo] | tuple[MonitorInfo, ...]) -> list[dict[str, Any]]:
    return [asdict(monitor) | {"width": monitor.width, "height": monitor.height, "label": monitor.label} for monitor in monitors]


def run_capture_diagnostic(
    capture: ScreenCapture,
    *,
    config: CaptureConfig,
    duration_s: float = 4.0,
    pause_s: float = 0.25,
    poll_interval_s: float = 0.05,
) -> CaptureDiagnosticResult:
    if duration_s < 0:
        raise ValueError("duration_s must be non-negative")
    if pause_s < 0:
        raise ValueError("pause_s must be non-negative")
    if poll_interval_s <= 0:
        raise ValueError("poll_interval_s must be positive")

    errors: list[str] = []
    checks: dict[str, bool] = {
        "monitors_detected": False,
        "capture_started": False,
        "frames_received": False,
        "latest_frame_available": False,
        "resolution_reported": False,
        "latency_reported": False,
        "backend_errors_zero": False,
        "pause_resume_called": False,
        "stopped_cleanly": False,
    }

    try:
        monitors = tuple(capture.list_monitors())
    except Exception as exc:
        monitors = ()
        errors.append(f"list_monitors: {type(exc).__name__}: {exc}")
    checks["monitors_detected"] = bool(monitors)

    try:
        capture.start()
        checks["capture_started"] = True
    except Exception as exc:
        errors.append(f"start: {type(exc).__name__}: {exc}")

    deadline = time.perf_counter() + duration_s
    pause_at = time.perf_counter() + (duration_s / 2.0)
    pause_done = False

    try:
        while checks["capture_started"] and time.perf_counter() < deadline:
            if pause_s and not pause_done and time.perf_counter() >= pause_at:
                capture.pause()
                time.sleep(pause_s)
                capture.resume()
                checks["pause_resume_called"] = True
                pause_done = True
            if capture.latest_frame() is not None:
                checks["latest_frame_available"] = True
            time.sleep(poll_interval_s)
    finally:
        try:
            capture.stop()
            checks["stopped_cleanly"] = True
        except Exception as exc:
            errors.append(f"stop: {type(exc).__name__}: {exc}")

    latest = capture.latest_frame()
    metrics = capture.metrics()
    checks["frames_received"] = metrics.frames_captured > 0
    checks["latest_frame_available"] = checks["latest_frame_available"] or latest is not None
    checks["resolution_reported"] = bool(metrics.latest_width and metrics.latest_height) or latest is not None
    checks["latency_reported"] = metrics.capture_latency_ms is not None
    checks["backend_errors_zero"] = metrics.backend_errors == 0

    latest_payload = None
    if latest is not None:
        latest_payload = {
            "sequence": latest.sequence,
            "timestamp": latest.timestamp,
            "width": latest.width,
            "height": latest.height,
            "latency_ms": latest.latency_ms,
            "metadata": latest.metadata,
        }

    return CaptureDiagnosticResult(
        config=config,
        monitors=monitors,
        checks=checks,
        metrics=metrics,
        latest_frame=latest_payload,
        errors=tuple(errors),
    )
