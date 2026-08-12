from __future__ import annotations

import numpy as np
from rtda.capture.frame import Frame
from rtda.models.perception import BoundingBox, ChangeDetectionResult, ChangeRegion
from rtda.perception.roi_processor import ROIProcessor


def test_roi_processor_work_elimination() -> None:
    processor = ROIProcessor()
    # 100x100 frame
    frame_data = np.zeros((100, 100, 4), dtype=np.uint8)
    frame = Frame(timestamp=1.0, width=100, height=100, data=frame_data, sequence=1)

    # Test 1: No change -> 0 ROIs, 100% work saved
    no_change = ChangeDetectionResult(
        changed=False,
        frame_sequence=1,
        previous_sequence=0,
        changed_pixels=0,
        changed_ratio=0.0,
        latency_ms=1.2,
        regions=(),
    )
    rois = processor.extract_rois(frame, no_change)
    assert len(rois) == 0
    assert processor.compute_work_saved_ratio(frame, rois) == 100.0

    # Test 2: Small change -> 1 ROI (20x20 area = 400 pixels out of 10,000 = 96% work saved!)
    region = ChangeRegion(
        bbox=BoundingBox(10, 10, 30, 30),
        area=400,
        changed_pixels=50,
        confidence=0.9,
    )
    with_change = ChangeDetectionResult(
        changed=True,
        frame_sequence=1,
        previous_sequence=0,
        changed_pixels=50,
        changed_ratio=0.04,
        latency_ms=1.5,
        regions=(region,),
    )
    rois_active = processor.extract_rois(frame, with_change)
    assert len(rois_active) == 1
    assert rois_active[0].data.shape == (20, 20, 4)
    saved_ratio = processor.compute_work_saved_ratio(frame, rois_active)
    assert saved_ratio >= 95.0
