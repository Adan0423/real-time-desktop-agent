from __future__ import annotations

import numpy as np

from rtda.capture.frame import Frame
from rtda.capture.frame_buffer import FrameBuffer
from rtda.capture.region import Region


def make_frame(sequence: int, width: int = 4, height: int = 3) -> Frame:
    data = np.arange(width * height * 4, dtype=np.uint8).reshape((height, width, 4))
    return Frame(timestamp=float(sequence), width=width, height=height, data=data, sequence=sequence)


def test_frame_buffer_keeps_latest_and_previous() -> None:
    buffer = FrameBuffer(max_size=2)
    buffer.push(make_frame(1))
    buffer.push(make_frame(2))
    buffer.push(make_frame(3))

    assert len(buffer) == 2
    assert buffer.dropped_frames == 1
    assert buffer.latest().sequence == 3
    assert buffer.previous().sequence == 2


def test_frame_region_returns_expected_shape() -> None:
    frame = make_frame(1, width=5, height=4)
    region = frame.get_region(Region(1, 1, 4, 3))

    assert region.width == 3
    assert region.height == 2
    assert region.data.shape == (2, 3, 4)
    assert region.metadata["parent_sequence"] == 1


def test_buffer_get_region_uses_latest_frame() -> None:
    buffer = FrameBuffer(max_size=3)
    buffer.push(make_frame(1))
    buffer.push(make_frame(2, width=6, height=5))

    region = buffer.get_region(Region(0, 0, 2, 2))

    assert region is not None
    assert region.sequence == 2
    assert region.data.shape == (2, 2, 4)


def test_latest_pair_is_a_consistent_snapshot() -> None:
    buffer = FrameBuffer(max_size=3)

    assert buffer.latest_pair() == (None, None)
    buffer.push(make_frame(1))
    assert buffer.latest_pair()[0] is None
    buffer.push(make_frame(2))

    previous, latest = buffer.latest_pair()

    assert previous.sequence == 1
    assert latest.sequence == 2
