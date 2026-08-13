from __future__ import annotations

import numpy as np
from rtda.capture.frame import Frame
from rtda.models.perception import BoundingBox, PerceptionElement, UIASnapshot
from rtda.perception.high_precision_pipeline import HighPrecisionPerceptionPipeline
from rtda.perception.ocr import DummyOCREngine, RapidOCREngine
from rtda.perception.interface import UIAutomationInspector


class FakeUIAInspector(UIAutomationInspector):
    def snapshot(self, *, window_title: str | None = None) -> UIASnapshot:
        elem = PerceptionElement(
            type="button",
            text="Submit",
            bbox=BoundingBox(10, 10, 50, 30),
            confidence=1.0,
            source="uia",
        )
        return UIASnapshot(timestamp=1.0, latency_ms=0.5, elements=(elem,))




class FakeRapidOCR:
    def __call__(self, image):
        # Return OCR result that doesn't overlap UIA to test deduplication & merging
        return [[[[100, 100], [200, 100], [200, 130], [100, 130]], "Cancel", 0.90]], None


def test_high_precision_pipeline_merges_uia_and_ocr() -> None:
    frame1 = Frame(timestamp=1.0, width=300, height=200, data=np.zeros((200, 300, 4), dtype=np.uint8), sequence=1)
    frame2 = Frame(timestamp=1.1, width=300, height=200, data=np.full((200, 300, 4), 255, dtype=np.uint8), sequence=2)

    pipeline = HighPrecisionPerceptionPipeline(
        uia_inspector=FakeUIAInspector(),
        ocr_engine=RapidOCREngine(ocr_client=FakeRapidOCR()),
    )

    analysis = pipeline.process_frame(current_frame=frame2, previous_frame=frame1)

    assert analysis.changed is True
    assert len(analysis.elements) == 2
    assert analysis.elements[0].text == "Submit"
    assert analysis.elements[0].source == "uia"
    assert analysis.elements[1].text == "Cancel"
    assert analysis.elements[1].source == "ocr_rapid"
    assert analysis.errors == ()
