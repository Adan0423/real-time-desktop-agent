from __future__ import annotations

import time
from dataclasses import dataclass

import cv2
import numpy as np

from rtda.capture.frame import Frame
from rtda.models.perception import BoundingBox, ChangeDetectionResult, ChangeRegion
from rtda.perception.interface import ChangeDetector


@dataclass(frozen=True, slots=True)
class ChangeDetectionConfig:
    threshold: int = 25
    min_area: int = 120
    min_changed_ratio: float = 0.0002
    downscale: float = 0.5
    blur_kernel: int = 3
    morph_kernel: int = 3
    dilate_iterations: int = 1
    max_regions: int = 24

    def __post_init__(self) -> None:
        if not 0 < self.threshold <= 255:
            raise ValueError("threshold must be between 1 and 255")
        if self.min_area < 0:
            raise ValueError("min_area must be non-negative")
        if self.min_changed_ratio < 0:
            raise ValueError("min_changed_ratio must be non-negative")
        if not 0 < self.downscale <= 1:
            raise ValueError("downscale must be in the range (0, 1]")
        if self.blur_kernel < 0 or (self.blur_kernel != 0 and self.blur_kernel % 2 == 0):
            raise ValueError("blur_kernel must be 0 or a positive odd number")
        if self.morph_kernel <= 0:
            raise ValueError("morph_kernel must be positive")
        if self.dilate_iterations < 0:
            raise ValueError("dilate_iterations must be non-negative")
        if self.max_regions <= 0:
            raise ValueError("max_regions must be positive")


class OpenCVChangeDetector(ChangeDetector):
    """Fast frame-diff detector for local UI change detection."""

    def __init__(self, config: ChangeDetectionConfig | None = None) -> None:
        self.config = config or ChangeDetectionConfig()

    def detect(self, previous: Frame, current: Frame) -> ChangeDetectionResult:
        if previous.width != current.width or previous.height != current.height:
            raise ValueError("frames must have the same dimensions")

        started = time.perf_counter()
        previous_gray = self._prepare(previous.data)
        current_gray = self._prepare(current.data)

        diff = cv2.absdiff(previous_gray, current_gray)
        _, mask = cv2.threshold(diff, self.config.threshold, 255, cv2.THRESH_BINARY)
        mask = self._denoise(mask)
        changed_pixels = int(cv2.countNonZero(mask))
        changed_ratio = changed_pixels / float(mask.shape[0] * mask.shape[1])
        regions = self._regions_from_mask(mask, current.width, current.height)
        changed = bool(regions) and changed_ratio >= self.config.min_changed_ratio
        latency_ms = (time.perf_counter() - started) * 1000.0

        return ChangeDetectionResult(
            changed=changed,
            frame_sequence=current.sequence,
            previous_sequence=previous.sequence,
            changed_pixels=changed_pixels,
            changed_ratio=changed_ratio,
            latency_ms=latency_ms,
            regions=regions,
        )

    def _prepare(self, data: np.ndarray) -> np.ndarray:
        if data.ndim == 2:
            gray = data
        elif data.ndim == 3 and data.shape[2] == 4:
            gray = cv2.cvtColor(data, cv2.COLOR_BGRA2GRAY)
        elif data.ndim == 3 and data.shape[2] == 3:
            gray = cv2.cvtColor(data, cv2.COLOR_BGR2GRAY)
        else:
            raise ValueError(f"unsupported frame shape: {data.shape}")

        if self.config.downscale < 1:
            gray = cv2.resize(
                gray,
                None,
                fx=self.config.downscale,
                fy=self.config.downscale,
                interpolation=cv2.INTER_AREA,
            )
        if self.config.blur_kernel:
            gray = cv2.GaussianBlur(gray, (self.config.blur_kernel, self.config.blur_kernel), 0)
        return gray

    def _denoise(self, mask: np.ndarray) -> np.ndarray:
        kernel = np.ones((self.config.morph_kernel, self.config.morph_kernel), dtype=np.uint8)
        clean = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        if self.config.dilate_iterations:
            clean = cv2.dilate(clean, kernel, iterations=self.config.dilate_iterations)
        return clean

    def _regions_from_mask(
        self,
        mask: np.ndarray,
        original_width: int,
        original_height: int,
    ) -> tuple[ChangeRegion, ...]:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        scale_x = original_width / mask.shape[1]
        scale_y = original_height / mask.shape[0]
        regions: list[ChangeRegion] = []

        for contour in contours:
            x, y, width, height = cv2.boundingRect(contour)
            bbox = BoundingBox(
                left=int(x * scale_x),
                top=int(y * scale_y),
                right=int((x + width) * scale_x),
                bottom=int((y + height) * scale_y),
            ).clamp(original_width, original_height)
            if bbox.area < self.config.min_area:
                continue

            changed_pixels = int(cv2.countNonZero(mask[y : y + height, x : x + width]))
            density = changed_pixels / float(max(1, width * height))
            confidence = min(1.0, max(0.05, density))
            regions.append(
                ChangeRegion(
                    bbox=bbox,
                    area=bbox.area,
                    changed_pixels=changed_pixels,
                    confidence=confidence,
                )
            )

        regions.sort(key=lambda region: region.area, reverse=True)
        return tuple(regions[: self.config.max_regions])
