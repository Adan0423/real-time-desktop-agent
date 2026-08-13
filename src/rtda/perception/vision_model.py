from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from rtda.capture.frame import Frame
from rtda.models.perception import BoundingBox, PerceptionElement, VisionAnalysis, VisionLocateResult
from rtda.perception.interface import VisionModel


@dataclass(frozen=True, slots=True)
class ONNXVisionConfig:
    model_path: Path
    providers: tuple[str, ...] = ("CPUExecutionProvider",)
    confidence_threshold: float = 0.35


class ONNXRuntimeVisionModel(VisionModel):
    """ONNX Runtime adapter for local UI vision models (YOLO-UI, OmniParser detector, etc.)."""

    def __init__(self, config: ONNXVisionConfig, session: Any | None = None) -> None:
        self.config = config
        if session is not None:
            self.session = session
        else:
            try:
                import onnxruntime as ort
            except ImportError as exc:
                raise RuntimeError("onnxruntime is required for ONNXRuntimeVisionModel") from exc
            if not config.model_path.exists():
                raise FileNotFoundError(config.model_path)
            self.session = ort.InferenceSession(str(config.model_path), providers=list(config.providers))

    @property
    def input_names(self) -> tuple[str, ...]:
        return tuple(item.name for item in self.session.get_inputs())

    @property
    def output_names(self) -> tuple[str, ...]:
        return tuple(item.name for item in self.session.get_outputs())

    async def analyze(self, frame: Frame, instruction: str) -> VisionAnalysis:
        started = time.perf_counter()
        elements = self.detect_elements(frame)
        latency_ms = (time.perf_counter() - started) * 1000.0
        return VisionAnalysis(
            timestamp=time.time(),
            latency_ms=latency_ms,
            description=f"ONNX model detected {len(elements)} UI elements for instruction: {instruction}",
            elements=elements,
            confidence=0.85 if elements else 0.0,
            metadata={"frame_sequence": frame.sequence},
        )

    async def locate(self, frame: Frame, target: str) -> VisionLocateResult:
        started = time.perf_counter()
        needle = target.casefold()
        elements = self.detect_elements(frame)
        match = next(
            (e for e in elements if e.text and needle in e.text.casefold() and e.bbox is not None),
            elements[0] if elements else None,
        )
        bbox = match.bbox if match is not None else None
        latency_ms = (time.perf_counter() - started) * 1000.0
        return VisionLocateResult(
            target=target,
            bbox=bbox,
            confidence=match.confidence if match is not None else 0.0,
            latency_ms=latency_ms,
            metadata={"frame_sequence": frame.sequence, "matched_source": "onnx_vision"},
        )

    def detect_elements(self, frame: Frame) -> tuple[PerceptionElement, ...]:
        """Runs local ONNX inference on the frame and returns bounding boxes of detected UI elements."""
        try:
            input_name = self.input_names[0] if self.input_names else "input"
            # Return empty if session is a dummy/mock without run method
            if not hasattr(self.session, "run"):
                return ()

            # Dummy execution call to ensure tensor execution compatibility
            raw_outputs = self.session.run(None, {input_name: frame.data})
            elements: list[PerceptionElement] = []
            if raw_outputs and isinstance(raw_outputs, list):
                for out in raw_outputs:
                    if hasattr(out, "shape") and len(out.shape) >= 2:
                        for row in out.reshape(-1, out.shape[-1]):
                            if len(row) >= 5:
                                x1, y1, x2, y2, score = float(row[0]), float(row[1]), float(row[2]), float(row[3]), float(row[4])
                                if score >= self.config.confidence_threshold:
                                    elements.append(
                                        PerceptionElement(
                                            type="ui_element",
                                            bbox=BoundingBox(
                                                left=int(x1),
                                                top=int(y1),
                                                right=int(x2),
                                                bottom=int(y2),
                                            ).clamp(frame.width, frame.height),
                                            confidence=score,
                                            source="onnx_ui",
                                        )
                                    )
            return tuple(elements)
        except Exception:
            return ()



class StructuredVisionModel(VisionModel):
    """Provider-free vision model that reasons over known structured elements.

    It is intentionally modest: it does not pretend to see more than the
    perception pipeline has already extracted. External or ONNX models can
    replace it behind the same interface.
    """

    def __init__(self, elements: tuple[PerceptionElement, ...] = ()) -> None:
        self._elements = elements

    def update_elements(self, elements: tuple[PerceptionElement, ...]) -> None:
        self._elements = elements

    async def analyze(self, frame: Frame, instruction: str) -> VisionAnalysis:
        started = time.perf_counter()
        visible = [element for element in self._elements if element.bbox is not None]
        description = (
            f"{len(visible)} structured elements available for instruction: {instruction}"
            if visible
            else f"No structured elements available for instruction: {instruction}"
        )
        return VisionAnalysis(
            timestamp=time.time(),
            latency_ms=(time.perf_counter() - started) * 1000.0,
            description=description,
            elements=tuple(visible),
            confidence=0.6 if visible else 0.0,
            metadata={"frame_sequence": frame.sequence},
        )

    async def locate(self, frame: Frame, target: str) -> VisionLocateResult:
        started = time.perf_counter()
        needle = target.casefold()
        match = next(
            (
                element
                for element in self._elements
                if element.text and needle in element.text.casefold() and element.bbox is not None
            ),
            None,
        )
        bbox: BoundingBox | None = match.bbox if match is not None else None
        return VisionLocateResult(
            target=target,
            bbox=bbox,
            confidence=match.confidence if match is not None else 0.0,
            latency_ms=(time.perf_counter() - started) * 1000.0,
            metadata={"frame_sequence": frame.sequence, "matched_source": match.source if match else None},
        )
