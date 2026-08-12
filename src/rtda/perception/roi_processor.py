from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from rtda.capture.frame import Frame
from rtda.models.perception import BoundingBox, ChangeDetectionResult, ChangeRegion


@dataclass(frozen=True, slots=True)
class ROICrop:
    bbox: BoundingBox
    data: Any  # cropped numpy array
    area: int
    changed_pixels: int
    sequence: int


@dataclass
class ROIProcessor:
    """Implements Work Elimination by cropping perception tasks to changed ROIs.

    If a frame has no detected changes, crop generation is skipped, avoiding
    costly full-screen OCR or visual inference on unchanged pixels.
    """

    min_area: int = 100
    max_rois: int = 5

    def extract_rois(self, frame: Frame, change_result: ChangeDetectionResult) -> list[ROICrop]:
        """Extract cropped ROI numpy arrays for changed regions only."""
        if not change_result.changed or not change_result.regions:
            return []

        # Sort regions by changed_pixels (most significant changes first)
        sorted_regions = sorted(change_result.regions, key=lambda r: r.changed_pixels, reverse=True)

        rois: list[ROICrop] = []
        for region in sorted_regions[: self.max_rois]:
            if region.area < self.min_area:
                continue

            bbox = region.bbox.clamp(frame.width, frame.height)
            try:
                # Crop numpy array: data[top:bottom, left:right]
                crop_data = frame.data[bbox.top : bbox.bottom, bbox.left : bbox.right]
                rois.append(
                    ROICrop(
                        bbox=bbox,
                        data=crop_data,
                        area=region.area,
                        changed_pixels=region.changed_pixels,
                        sequence=frame.sequence,
                    )
                )
            except Exception:
                pass

        return rois

    def compute_work_saved_ratio(self, frame: Frame, rois: list[ROICrop]) -> float:
        """Calculate the percentage of pixels/computation saved by using ROI processing."""
        total_pixels = frame.width * frame.height
        if total_pixels <= 0 or not rois:
            return 100.0  # 100% saved if no ROIs needed

        roi_pixels = sum(r.bbox.area for r in rois)
        saved = max(0.0, 1.0 - (roi_pixels / total_pixels)) * 100.0
        return round(saved, 1)
