from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.typing import NDArray

from rtda.capture.region import Region


@dataclass(slots=True)
class Frame:
    """A captured frame kept in memory."""

    timestamp: float
    width: int
    height: int
    data: NDArray[np.generic]
    sequence: int = 0
    source_timestamp: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("frame dimensions must be positive")
        if self.data.ndim < 2:
            raise ValueError("frame data must have at least height and width dimensions")
        if self.data.shape[0] != self.height or self.data.shape[1] != self.width:
            raise ValueError("frame dimensions must match numpy array shape")

    @property
    def latency_ms(self) -> float | None:
        if self.source_timestamp is None:
            return None
        return max(0.0, (self.timestamp - self.source_timestamp) * 1000.0)

    def get_region(self, region: Region, *, copy: bool = False) -> "Frame":
        safe_region = region.clamp(self.width, self.height)
        view = self.data[
            safe_region.top : safe_region.bottom,
            safe_region.left : safe_region.right,
            ...,
        ]
        if copy:
            view = view.copy()
        metadata = dict(self.metadata)
        metadata["parent_sequence"] = self.sequence
        metadata["region"] = safe_region.to_tuple()
        return Frame(
            timestamp=self.timestamp,
            width=safe_region.width,
            height=safe_region.height,
            data=view,
            sequence=self.sequence,
            source_timestamp=self.source_timestamp,
            metadata=metadata,
        )
