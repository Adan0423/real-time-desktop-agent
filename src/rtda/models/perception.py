from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True, slots=True)
class BoundingBox:
    left: int
    top: int
    right: int
    bottom: int

    def __post_init__(self) -> None:
        if self.right <= self.left:
            raise ValueError("bbox.right must be greater than bbox.left")
        if self.bottom <= self.top:
            raise ValueError("bbox.bottom must be greater than bbox.top")

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top

    @property
    def area(self) -> int:
        return self.width * self.height

    @classmethod
    def from_xywh(cls, x: int, y: int, width: int, height: int) -> "BoundingBox":
        return cls(left=x, top=y, right=x + width, bottom=y + height)

    def clamp(self, width: int, height: int) -> "BoundingBox":
        left = min(max(self.left, 0), width - 1)
        top = min(max(self.top, 0), height - 1)
        right = min(max(self.right, left + 1), width)
        bottom = min(max(self.bottom, top + 1), height)
        return BoundingBox(left, top, right, bottom)

    def intersects(self, other: "BoundingBox") -> bool:
        return not (
            self.right <= other.left
            or other.right <= self.left
            or self.bottom <= other.top
            or other.bottom <= self.top
        )

    def to_tuple(self) -> tuple[int, int, int, int]:
        return (self.left, self.top, self.right, self.bottom)


PerceptionSource = Literal["uia", "ocr", "opencv", "vision_ai"]


@dataclass(frozen=True, slots=True)
class PerceptionElement:
    type: str
    bbox: BoundingBox
    confidence: float
    source: PerceptionSource
    text: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ChangeRegion:
    bbox: BoundingBox
    area: int
    changed_pixels: int
    confidence: float
    source: Literal["opencv"] = "opencv"


@dataclass(frozen=True, slots=True)
class ChangeDetectionResult:
    changed: bool
    frame_sequence: int
    previous_sequence: int
    changed_pixels: int
    changed_ratio: float
    latency_ms: float
    regions: tuple[ChangeRegion, ...]
    source: Literal["opencv"] = "opencv"

    @property
    def region_count(self) -> int:
        return len(self.regions)


@dataclass(frozen=True, slots=True)
class OCRResult:
    timestamp: float
    latency_ms: float
    elements: tuple[PerceptionElement, ...]
    source: Literal["ocr"] = "ocr"
    errors: tuple[str, ...] = ()

    @property
    def text_count(self) -> int:
        return len(self.elements)


@dataclass(frozen=True, slots=True)
class UIAElement:
    name: str
    control_type: str
    bbox: BoundingBox | None
    enabled: bool | None
    offscreen: bool | None
    automation_id: str | None = None
    class_name: str | None = None
    process_id: int | None = None
    native_window_handle: int | None = None
    depth: int = 0
    path: str = ""
    child_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_perception_element(self) -> PerceptionElement | None:
        if self.bbox is None:
            return None
        return PerceptionElement(
            type=self.control_type,
            text=self.name or None,
            bbox=self.bbox,
            confidence=1.0,
            source="uia",
            metadata={
                "automation_id": self.automation_id,
                "class_name": self.class_name,
                "process_id": self.process_id,
                "native_window_handle": self.native_window_handle,
                "depth": self.depth,
                "path": self.path,
                **self.metadata,
            },
        )


@dataclass(frozen=True, slots=True)
class UIASnapshot:
    timestamp: float
    latency_ms: float
    elements: tuple[UIAElement, ...]
    root: UIAElement | None = None
    window_title: str | None = None
    truncated: bool = False
    errors: tuple[str, ...] = ()
    source: Literal["uia"] = "uia"

    @property
    def element_count(self) -> int:
        return len(self.elements)

    def to_perception_elements(self) -> tuple[PerceptionElement, ...]:
        return tuple(
            element
            for uia_element in self.elements
            if (element := uia_element.to_perception_element()) is not None
        )


@dataclass(frozen=True, slots=True)
class VisionAnalysis:
    timestamp: float
    latency_ms: float
    description: str
    elements: tuple[PerceptionElement, ...] = ()
    confidence: float = 0.0
    source: Literal["vision_ai"] = "vision_ai"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class VisionLocateResult:
    target: str
    bbox: BoundingBox | None
    confidence: float
    latency_ms: float
    source: Literal["vision_ai"] = "vision_ai"
    metadata: dict[str, Any] = field(default_factory=dict)
