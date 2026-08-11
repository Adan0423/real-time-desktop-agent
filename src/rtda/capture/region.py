from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Region:
    """Rectangular area in local frame coordinates."""

    left: int
    top: int
    right: int
    bottom: int

    def __post_init__(self) -> None:
        if self.right <= self.left:
            raise ValueError("region.right must be greater than region.left")
        if self.bottom <= self.top:
            raise ValueError("region.bottom must be greater than region.top")
        if self.left < 0 or self.top < 0:
            raise ValueError("region coordinates must be non-negative")

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top

    def to_tuple(self) -> tuple[int, int, int, int]:
        return (self.left, self.top, self.right, self.bottom)

    def clamp(self, width: int, height: int) -> "Region":
        left = min(max(self.left, 0), width)
        top = min(max(self.top, 0), height)
        right = min(max(self.right, left + 1), width)
        bottom = min(max(self.bottom, top + 1), height)
        return Region(left, top, right, bottom)
