from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import numpy as np

from rtda.capture.frame import Frame
from rtda.models.perception import BoundingBox, OCRResult, PerceptionElement
from rtda.perception.interface import OCREngine


@dataclass(frozen=True, slots=True)
class OCRConfig:
    language: str = "en"
    min_confidence: float = 0.45
    use_angle_cls: bool = False

    def __post_init__(self) -> None:
        if not 0 <= self.min_confidence <= 1:
            raise ValueError("min_confidence must be in [0, 1]")


class PaddleOCREngine(OCREngine):
    """PaddleOCR adapter. Imports Paddle only when OCR is instantiated."""

    def __init__(self, config: OCRConfig | None = None, ocr_client: Any | None = None) -> None:
        self.config = config or OCRConfig()
        if ocr_client is not None:
            self._ocr = ocr_client
            return
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:
            raise RuntimeError(
                "PaddleOCR is not installed or PaddlePaddle is unavailable for this Python. "
                "Install a compatible environment, then run: python -m pip install -e .[ocr]"
            ) from exc

        self._ocr = PaddleOCR(lang=self.config.language, use_angle_cls=self.config.use_angle_cls)

    def analyze(self, frame: Frame) -> OCRResult:
        started = time.perf_counter()
        image = self._to_ocr_image(frame.data)
        errors: list[str] = []
        raw: Any
        try:
            if hasattr(self._ocr, "ocr"):
                raw = self._ocr.ocr(image, cls=self.config.use_angle_cls)
            else:
                raw = self._ocr.predict(image)
        except Exception as exc:
            latency_ms = (time.perf_counter() - started) * 1000.0
            return OCRResult(
                timestamp=time.time(),
                latency_ms=latency_ms,
                elements=(),
                errors=(f"{type(exc).__name__}: {exc}",),
            )

        elements = tuple(self._parse_raw_result(raw))
        if not elements and raw:
            errors.append("OCR result format was not recognized")
        latency_ms = (time.perf_counter() - started) * 1000.0
        return OCRResult(timestamp=time.time(), latency_ms=latency_ms, elements=elements, errors=tuple(errors))

    def _parse_raw_result(self, raw: Any) -> list[PerceptionElement]:
        elements: list[PerceptionElement] = []
        for item in self._iter_v2_items(raw):
            parsed = self._parse_v2_item(item)
            if parsed is not None:
                elements.append(parsed)
        if elements:
            return elements
        for result in self._iter_dict_results(raw):
            elements.extend(self._parse_dict_result(result))
        return elements

    def _iter_v2_items(self, raw: Any):
        if raw is None:
            return
        pages = raw if isinstance(raw, list) else [raw]
        for page in pages:
            if page is None:
                continue
            if self._looks_like_v2_item(page):
                yield page
                continue
            if isinstance(page, list) and page and isinstance(page[0], list):
                for item in page:
                    if self._looks_like_v2_item(item):
                        yield item

    def _parse_v2_item(self, item: Any) -> PerceptionElement | None:
        try:
            points = item[0]
            text, score = item[1]
        except Exception:
            return None
        confidence = float(score)
        if confidence < self.config.min_confidence:
            return None
        bbox = self._bbox_from_points(points)
        if bbox is None:
            return None
        return PerceptionElement(type="text", text=str(text), bbox=bbox, confidence=confidence, source="ocr")

    def _iter_dict_results(self, raw: Any):
        if raw is None:
            return
        items = raw if isinstance(raw, list) else [raw]
        for item in items:
            if isinstance(item, dict):
                yield item
            elif hasattr(item, "to_dict"):
                yield item.to_dict()

    def _parse_dict_result(self, result: dict[str, Any]) -> list[PerceptionElement]:
        texts = result.get("rec_texts") or result.get("texts") or []
        scores = result.get("rec_scores") or result.get("scores") or [1.0] * len(texts)
        boxes = result.get("dt_polys") or result.get("rec_polys") or result.get("boxes") or []
        elements: list[PerceptionElement] = []
        for text, score, box in zip(texts, scores, boxes):
            confidence = float(score)
            if confidence < self.config.min_confidence:
                continue
            bbox = self._bbox_from_points(box)
            if bbox is None:
                continue
            elements.append(
                PerceptionElement(type="text", text=str(text), bbox=bbox, confidence=confidence, source="ocr")
            )
        return elements

    @staticmethod
    def _bbox_from_points(points: Any) -> BoundingBox | None:
        array = np.asarray(points, dtype=np.float32)
        if array.size < 4:
            return None
        array = array.reshape((-1, 2))
        left = int(np.floor(array[:, 0].min()))
        top = int(np.floor(array[:, 1].min()))
        right = int(np.ceil(array[:, 0].max()))
        bottom = int(np.ceil(array[:, 1].max()))
        if right <= left or bottom <= top:
            return None
        return BoundingBox(left=left, top=top, right=right, bottom=bottom)

    @staticmethod
    def _looks_like_v2_item(item: Any) -> bool:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            return False
        second = item[1]
        return isinstance(second, (list, tuple)) and len(second) >= 2

    @staticmethod
    def _to_ocr_image(data: np.ndarray) -> np.ndarray:
        if data.ndim == 3 and data.shape[2] == 4:
            return data[:, :, :3].copy()
        if data.ndim == 3 and data.shape[2] == 3:
            return data.copy()
        if data.ndim == 2:
            return data.copy()
        raise ValueError(f"unsupported frame shape for OCR: {data.shape}")


class RapidOCREngine(OCREngine):
    """RapidOCR adapter using rapidocr_onnxruntime or rapidocr. Imports ONNX OCR client gracefully."""

    def __init__(self, config: OCRConfig | None = None, ocr_client: Any | None = None) -> None:
        self.config = config or OCRConfig()
        if ocr_client is not None:
            self._ocr = ocr_client
            return
        try:
            from rapidocr_onnxruntime import RapidOCR

            self._ocr = RapidOCR()
        except ImportError:
            try:
                from rapidocr import RapidOCR

                self._ocr = RapidOCR()
            except ImportError as exc:
                raise RuntimeError(
                    "RapidOCR is not installed. Install via: pip install rapidocr-onnxruntime"
                ) from exc

    def analyze(self, frame: Frame) -> OCRResult:
        started = time.perf_counter()
        image = PaddleOCREngine._to_ocr_image(frame.data)
        errors: list[str] = []
        try:
            res = self._ocr(image)
            result = res[0] if isinstance(res, (tuple, list)) and len(res) > 0 else res
        except Exception as exc:
            latency_ms = (time.perf_counter() - started) * 1000.0
            return OCRResult(
                timestamp=time.time(),
                latency_ms=latency_ms,
                elements=(),
                errors=(f"{type(exc).__name__}: {exc}",),
            )

        elements: list[PerceptionElement] = []
        if result:
            for item in result:
                if not isinstance(item, (list, tuple)) or len(item) < 3:
                    continue
                box, text, score = item[0], item[1], float(item[2])
                if score < self.config.min_confidence:
                    continue
                bbox = PaddleOCREngine._bbox_from_points(box)
                if bbox is not None:
                    elements.append(
                        PerceptionElement(
                            type="text",
                            text=str(text),
                            bbox=bbox,
                            confidence=score,
                            source="ocr_rapid",
                        )
                    )

        latency_ms = (time.perf_counter() - started) * 1000.0
        return OCRResult(
            timestamp=time.time(),
            latency_ms=latency_ms,
            elements=tuple(elements),
            errors=tuple(errors),
        )


class DummyOCREngine(OCREngine):
    """Fallback OCR Engine when no physical OCR library is installed."""

    def analyze(self, frame: Frame) -> OCRResult:
        return OCRResult(timestamp=time.time(), latency_ms=0.0, elements=(), errors=())


class AutoOCREngine(OCREngine):
    """Smart OCR Engine that tries available local OCR implementations (RapidOCR -> PaddleOCR -> Fallback)."""

    def __init__(self, config: OCRConfig | None = None, preferred_engine: OCREngine | None = None) -> None:
        self.config = config or OCRConfig()
        self._engine: OCREngine = preferred_engine if preferred_engine is not None else self._autodetect_engine()

    def _autodetect_engine(self) -> OCREngine:
        try:
            return RapidOCREngine(config=self.config)
        except Exception:
            pass
        try:
            return PaddleOCREngine(config=self.config)
        except Exception:
            pass
        return DummyOCREngine()

    def analyze(self, frame: Frame) -> OCRResult:
        return self._engine.analyze(frame)

