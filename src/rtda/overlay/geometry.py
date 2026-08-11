from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from rtda.capture.interface import CaptureConfig, MonitorInfo


@dataclass(frozen=True, slots=True)
class OverlayRect:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return max(0, self.right - self.left)

    @property
    def height(self) -> int:
        return max(0, self.bottom - self.top)

    @property
    def valid(self) -> bool:
        return self.width > 0 and self.height > 0

    def expanded(self, pixels: int) -> "OverlayRect":
        return OverlayRect(
            self.left - pixels,
            self.top - pixels,
            self.right + pixels,
            self.bottom + pixels,
        )


WindowResolver = Callable[[str], OverlayRect | None]


def capture_rect_from_config(
    config: CaptureConfig,
    monitors: Sequence[MonitorInfo],
    *,
    window_resolver: WindowResolver | None = None,
) -> OverlayRect | None:
    if config.window_title:
        if window_resolver is None:
            from rtda.overlay.windows import find_window_rect_by_title

            window_resolver = find_window_rect_by_title
        return window_resolver(config.window_title)

    if not monitors:
        return None
    monitor = _select_monitor(monitors, config.monitor_index)
    if monitor is None:
        return None
    if config.region is None:
        return OverlayRect(monitor.left, monitor.top, monitor.right, monitor.bottom)

    region = config.region.clamp(monitor.width, monitor.height)
    return OverlayRect(
        monitor.left + region.left,
        monitor.top + region.top,
        monitor.left + region.right,
        monitor.top + region.bottom,
    )


def _select_monitor(monitors: Sequence[MonitorInfo], index: int) -> MonitorInfo | None:
    for monitor in monitors:
        if monitor.index == index:
            return monitor
    if 0 <= index < len(monitors):
        return monitors[index]
    return None
