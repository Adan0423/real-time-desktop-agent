from __future__ import annotations

import numpy as np

from rtda.capture.frame import Frame
from rtda.models.perception import BoundingBox
from rtda.perception.opencv_detector import ChangeDetectionConfig, OpenCVChangeDetector


def make_frame(sequence: int, data: np.ndarray) -> Frame:
    return Frame(
        timestamp=float(sequence),
        width=data.shape[1],
        height=data.shape[0],
        data=data,
        sequence=sequence,
    )


def test_detector_reports_no_change_for_identical_frames() -> None:
    data = np.zeros((48, 64, 4), dtype=np.uint8)
    detector = OpenCVChangeDetector(ChangeDetectionConfig(min_area=10, blur_kernel=0))

    result = detector.detect(make_frame(1, data), make_frame(2, data.copy()))

    assert result.changed is False
    assert result.region_count == 0
    assert result.changed_pixels == 0


def test_detector_finds_changed_region() -> None:
    before = np.zeros((80, 100, 4), dtype=np.uint8)
    after = before.copy()
    after[20:42, 30:58, :] = 255
    detector = OpenCVChangeDetector(
        ChangeDetectionConfig(threshold=10, min_area=50, blur_kernel=0, dilate_iterations=0)
    )

    result = detector.detect(make_frame(1, before), make_frame(2, after))

    assert result.changed is True
    assert result.region_count == 1
    assert result.regions[0].bbox.intersects(BoundingBox(30, 20, 58, 42))
    assert result.changed_ratio > 0


def test_detector_rejects_dimension_mismatch() -> None:
    first = make_frame(1, np.zeros((20, 20, 4), dtype=np.uint8))
    second = make_frame(2, np.zeros((30, 20, 4), dtype=np.uint8))
    detector = OpenCVChangeDetector()

    try:
        detector.detect(first, second)
    except ValueError as exc:
        assert "same dimensions" in str(exc)
    else:
        raise AssertionError("expected ValueError")
