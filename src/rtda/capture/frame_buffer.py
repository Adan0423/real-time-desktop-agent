from __future__ import annotations

from collections import deque
from threading import Lock

from rtda.capture.frame import Frame
from rtda.capture.region import Region


class FrameBuffer:
    """Thread-safe latest-frame ring buffer."""

    def __init__(self, max_size: int = 8) -> None:
        if max_size <= 0:
            raise ValueError("max_size must be positive")
        self._frames: deque[Frame] = deque(maxlen=max_size)
        self._lock = Lock()
        self._dropped_frames = 0

    @property
    def max_size(self) -> int:
        return self._frames.maxlen or 0

    @property
    def dropped_frames(self) -> int:
        with self._lock:
            return self._dropped_frames

    def __len__(self) -> int:
        with self._lock:
            return len(self._frames)

    def clear(self) -> None:
        with self._lock:
            self._frames.clear()
            self._dropped_frames = 0

    def push(self, frame: Frame) -> int:
        """Push a frame and return the number of frames dropped by this push."""

        with self._lock:
            dropped = 1 if len(self._frames) == self.max_size else 0
            self._frames.append(frame)
            self._dropped_frames += dropped
            return dropped

    def latest(self) -> Frame | None:
        with self._lock:
            return self._frames[-1] if self._frames else None

    def previous(self) -> Frame | None:
        with self._lock:
            return self._frames[-2] if len(self._frames) >= 2 else None

    def get_region(self, region: Region, *, copy: bool = False) -> Frame | None:
        frame = self.latest()
        if frame is None:
            return None
        return frame.get_region(region, copy=copy)
