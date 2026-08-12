from __future__ import annotations

import pytest

from rtda.capture.region import Region


def test_region_validates_dimensions() -> None:
    with pytest.raises(ValueError):
        Region(10, 0, 10, 20)
    with pytest.raises(ValueError):
        Region(0, 5, 10, 5)


def test_region_clamps_to_frame_size() -> None:
    region = Region(5, 5, 20, 20)

    clamped = region.clamp(12, 10)

    assert clamped.to_tuple() == (5, 5, 12, 10)
