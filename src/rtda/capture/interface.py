from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

from rtda.capture.frame import Frame
from rtda.capture.region import Region

CaptureBackend = Literal["wgc", "dxgi"]
MAX_CAPTURE_BUFFER_SIZE = 4


@dataclass(frozen=True, slots=True)
class MonitorInfo:
    index: int
    handle: int
    left: int
    top: int
    right: int
    bottom: int
    primary: bool
    device_name: str

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top

    @property
    def label(self) -> str:
        marker = "primary" if self.primary else "secondary"
        return f"{self.index}: {self.device_name} {self.width}x{self.height} ({marker})"


@dataclass(frozen=True, slots=True)
class CaptureConfig:
    target_fps: int = 60
    max_buffer_size: int = 2
    monitor_index: int = 0
    region: Region | None = None
    backend: CaptureBackend = "dxgi"
    window_title: str | None = None
    capture_cursor: bool = True
    draw_border: bool = False

    def __post_init__(self) -> None:
        if self.target_fps <= 0:
            raise ValueError("target_fps must be positive")
        if self.max_buffer_size <= 0:
            raise ValueError("max_buffer_size must be positive")
        if self.max_buffer_size > MAX_CAPTURE_BUFFER_SIZE:
            raise ValueError(f"max_buffer_size must be <= {MAX_CAPTURE_BUFFER_SIZE}")
        if self.monitor_index < 0:
            raise ValueError("monitor_index must be non-negative")
        if self.backend not in ("wgc", "dxgi"):
            raise ValueError("backend must be 'wgc' or 'dxgi'")
        if self.window_title and self.backend != "wgc":
            raise ValueError("window_title capture requires backend='wgc'")


@dataclass(frozen=True, slots=True)
class CaptureStats:
    capture_fps: float
    capture_latency_ms: float | None
    frames_captured: int
    buffer_dropped_frames: int
    estimated_missed_frames: int
    backend_errors: int
    uptime_s: float
    latest_width: int | None = None
    latest_height: int | None = None


class ScreenCapture(ABC):
    @abstractmethod
    def list_monitors(self) -> list[MonitorInfo]:
        raise NotImplementedError

    @abstractmethod
    def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def pause(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def resume(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def latest_frame(self) -> Frame | None:
        raise NotImplementedError

    @abstractmethod
    def get_fps(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def get_latency(self) -> float | None:
        raise NotImplementedError

    @abstractmethod
    def metrics(self) -> CaptureStats:
        raise NotImplementedError
