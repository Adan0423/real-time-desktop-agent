from __future__ import annotations

import numpy as np

from rtda.capture.frame import Frame
from rtda.perception.ocr import OCRConfig, PaddleOCREngine


class FakePaddleOCR:
    def ocr(self, image, cls=False):
        assert image.shape == (20, 30, 3)
        return [[[[1, 2], [11, 2], [11, 8], [1, 8]], ("Guardar", 0.92)]]


def test_paddle_ocr_engine_parses_v2_result() -> None:
    frame = Frame(timestamp=1.0, width=30, height=20, data=np.zeros((20, 30, 4), dtype=np.uint8), sequence=1)
    engine = PaddleOCREngine(OCRConfig(min_confidence=0.5), ocr_client=FakePaddleOCR())

    result = engine.analyze(frame)

    assert result.text_count == 1
    assert result.elements[0].text == "Guardar"
    assert result.elements[0].bbox.to_tuple() == (1, 2, 11, 8)
    assert result.errors == ()
