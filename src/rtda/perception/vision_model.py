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


class ONNXRuntimeVisionModel:
    """Thin ONNX Runtime adapter for future local vision models."""

    def __init__(self, config: ONNXVisionConfig) -> None:
        try:
            import onnxruntime as ort
        except ImportError as exc:
            raise RuntimeError("onnxruntime is required for ONNXRuntimeVisionModel") from exc
        if not config.model_path.exists():
            raise FileNotFoundError(config.model_path)
        self.config = config
        self.session = ort.InferenceSession(str(config.model_path), providers=list(config.providers))

    @property
    def input_names(self) -> tuple[str, ...]:
        return tuple(item.name for item in self.session.get_inputs())

    @property
    def output_names(self) -> tuple[str, ...]:
        return tuple(item.name for item in self.session.get_outputs())


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
