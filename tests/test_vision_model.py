from __future__ import annotations

import asyncio

import numpy as np

from rtda.capture.frame import Frame
from rtda.models.perception import BoundingBox, PerceptionElement
from rtda.perception.vision_model import StructuredVisionModel


def test_structured_vision_model_locates_known_element() -> None:
    frame = Frame(timestamp=1.0, width=10, height=10, data=np.zeros((10, 10, 4), dtype=np.uint8), sequence=1)
    model = StructuredVisionModel(
        (
            PerceptionElement(
                type="ButtonControl",
                text="Guardar",
                bbox=BoundingBox(1, 2, 5, 6),
                confidence=0.8,
                source="uia",
            ),
        )
    )

    result = asyncio.run(model.locate(frame, "Guardar"))

    assert result.bbox == BoundingBox(1, 2, 5, 6)
    assert result.confidence == 0.8


def test_structured_vision_model_analyzes_available_elements() -> None:
    frame = Frame(timestamp=1.0, width=10, height=10, data=np.zeros((10, 10, 4), dtype=np.uint8), sequence=1)
    model = StructuredVisionModel()

    result = asyncio.run(model.analyze(frame, "describe"))

    assert "No structured elements" in result.description
