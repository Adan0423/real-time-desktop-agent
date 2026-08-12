from __future__ import annotations

import numpy as np

from rtda.capture.frame import Frame
from rtda.capture.frame_buffer import FrameBuffer
from rtda.perception.change_detector import FrameChangeProcessor
from rtda.perception.opencv_detector import ChangeDetectionConfig, OpenCVChangeDetector


def make_frame(sequence: int, fill: int) -> Frame:
    data = np.full((32, 32, 4), fill, dtype=np.uint8)
    return Frame(timestamp=float(sequence), width=32, height=32, data=data, sequence=sequence)


def test_processor_requires_two_frames() -> None:
    buffer = FrameBuffer(max_size=4)
    processor = FrameChangeProcessor(OpenCVChangeDetector())

    assert processor.process_buffer(buffer) is None
    buffer.push(make_frame(1, 0))
    assert processor.process_buffer(buffer) is None


def test_processor_skips_already_processed_latest_frame() -> None:
    buffer = FrameBuffer(max_size=4)
    buffer.push(make_frame(1, 0))
    buffer.push(make_frame(2, 255))
    processor = FrameChangeProcessor(
        OpenCVChangeDetector(ChangeDetectionConfig(threshold=10, min_area=1, blur_kernel=0))
    )

    assert processor.process_buffer(buffer) is not None
    assert processor.process_buffer(buffer) is None
    assert processor.metrics.snapshot().frames_processed == 1
