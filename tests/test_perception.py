from __future__ import annotations

import asyncio
import numpy as np
import pytest

from rtda.capture.frame import Frame
from rtda.capture.frame_buffer import FrameBuffer
from rtda.models.perception import BoundingBox, ChangeDetectionResult, ChangeRegion, PerceptionElement, UIASnapshot
from rtda.perception.change_detector import FrameChangeProcessor
from rtda.perception.high_precision_pipeline import HighPrecisionPerceptionPipeline
from rtda.perception.interface import UIAutomationInspector
from rtda.perception.ocr import AutoOCREngine, DummyOCREngine, OCRConfig, PaddleOCREngine, RapidOCREngine
from rtda.perception.opencv_detector import ChangeDetectionConfig, OpenCVChangeDetector
from rtda.perception.roi_processor import ROIProcessor
from rtda.perception.uia import UIAConfig, WindowsUIAutomationInspector, summarize_uia_elements
from rtda.perception.vision_model import StructuredVisionModel


def make_frame(sequence: int, data: np.ndarray) -> Frame:
    return Frame(
        timestamp=float(sequence),
        width=data.shape[1],
        height=data.shape[0],
        data=data,
        sequence=sequence,
    )


# ── UIA Inspector Tests ──────────────────────────────────────────────────────

class FakeRect:
    def __init__(self, left: int, top: int, right: int, bottom: int) -> None:
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom


class FakeControl:
    def __init__(
        self,
        *,
        name: str,
        control_type: str = "ButtonControl",
        rect: FakeRect | None = None,
        children: list["FakeControl"] | None = None,
        offscreen: bool = False,
    ) -> None:
        self.Name = name
        self.ControlTypeName = control_type
        self.AutomationId = f"{name}-id" if name else ""
        self.ClassName = "FakeClass"
        self.BoundingRectangle = rect
        self.IsEnabled = True
        self.IsOffscreen = offscreen
        self.ProcessId = 123
        self.NativeWindowHandle = 456
        self._children = children or []

    def GetChildren(self) -> list["FakeControl"]:
        return self._children


class FakeInspector(WindowsUIAutomationInspector):
    def __init__(self, root: FakeControl, config: UIAConfig | None = None) -> None:
        super().__init__(config)
        self.root = root

    def _resolve_root(self, window_title: str | None):
        return self.root


def test_uia_snapshot_collects_structured_elements() -> None:
    child = FakeControl(name="Save", rect=FakeRect(10, 20, 70, 42))
    root = FakeControl(
        name="Window",
        control_type="WindowControl",
        rect=FakeRect(0, 0, 100, 80),
        children=[child],
    )
    inspector = FakeInspector(root, UIAConfig(max_depth=2))

    snapshot = inspector.snapshot()

    assert snapshot.element_count == 2
    assert snapshot.root is not None
    assert snapshot.elements[1].name == "Save"
    assert snapshot.elements[1].bbox == BoundingBox(10, 20, 70, 42)
    assert snapshot.to_perception_elements()[1].source == "uia"


def test_uia_snapshot_filters_offscreen_and_truncates() -> None:
    visible = FakeControl(name="Visible", rect=FakeRect(0, 0, 10, 10))
    hidden = FakeControl(name="Hidden", rect=FakeRect(0, 0, 10, 10), offscreen=True)
    root = FakeControl(name="Root", rect=FakeRect(0, 0, 20, 20), children=[visible, hidden])
    inspector = FakeInspector(root, UIAConfig(max_depth=1, max_elements=2, include_offscreen=False))

    snapshot = inspector.snapshot()

    assert snapshot.truncated is True
    assert all(element.name != "Hidden" for element in snapshot.elements)


def test_uia_snapshot_filters_elements_outside_root_bounds() -> None:
    outside = FakeControl(name="Outside", rect=FakeRect(-32000, -32000, -31984, -31984))
    root = FakeControl(name="Root", rect=FakeRect(0, 0, 100, 100), children=[outside])
    inspector = FakeInspector(root, UIAConfig(max_depth=1, exclude_outside_root=True))

    snapshot = inspector.snapshot()

    assert [element.name for element in snapshot.elements] == ["Root"]


def test_summarize_uia_elements_is_json_ready() -> None:
    root = FakeControl(name="Root", rect=FakeRect(1, 2, 3, 4))
    snapshot = FakeInspector(root).snapshot()

    summary = summarize_uia_elements(snapshot.elements)

    assert summary[0]["bbox"] == (1, 2, 3, 4)
    assert summary[0]["name"] == "Root"


# ── OpenCV Change Detector Tests ─────────────────────────────────────────────

def test_detector_reports_no_change_for_identical_frames() -> None:
    data = np.zeros((48, 64, 4), dtype=np.uint8)
    detector = OpenCVChangeDetector(ChangeDetectionConfig(min_area=10, blur_kernel=0))

    result = detector.detect(make_frame(1, data), make_frame(2, data.copy()))

    assert result.changed is False
    assert result.region_count == 0
    assert result.changed_pixels == 0


def test_detector_finds_changed_region() -> None:
    before = np.zeros((80, 100, 4), dtype=np.uint8)
    after = before.copy()
    after[20:42, 30:58, :] = 255
    detector = OpenCVChangeDetector(
        ChangeDetectionConfig(threshold=10, min_area=50, blur_kernel=0, dilate_iterations=0)
    )

    result = detector.detect(make_frame(1, before), make_frame(2, after))

    assert result.changed is True
    assert result.region_count == 1
    assert result.regions[0].bbox.intersects(BoundingBox(30, 20, 58, 42))
    assert result.changed_ratio > 0


def test_detector_rejects_dimension_mismatch() -> None:
    first = make_frame(1, np.zeros((20, 20, 4), dtype=np.uint8))
    second = make_frame(2, np.zeros((30, 20, 4), dtype=np.uint8))
    detector = OpenCVChangeDetector()

    try:
        detector.detect(first, second)
    except ValueError as exc:
        assert "same dimensions" in str(exc)
    else:
        raise AssertionError("expected ValueError")


# ── ROI Processor Tests ──────────────────────────────────────────────────────

def test_roi_processor_work_elimination() -> None:
    processor = ROIProcessor()
    frame_data = np.zeros((100, 100, 4), dtype=np.uint8)
    frame = Frame(timestamp=1.0, width=100, height=100, data=frame_data, sequence=1)

    no_change = ChangeDetectionResult(
        changed=False,
        frame_sequence=1,
        previous_sequence=0,
        changed_pixels=0,
        changed_ratio=0.0,
        latency_ms=1.2,
        regions=(),
    )
    rois = processor.extract_rois(frame, no_change)
    assert len(rois) == 0
    assert processor.compute_work_saved_ratio(frame, rois) == 100.0

    region = ChangeRegion(
        bbox=BoundingBox(10, 10, 30, 30),
        area=400,
        changed_pixels=50,
        confidence=0.9,
    )
    with_change = ChangeDetectionResult(
        changed=True,
        frame_sequence=1,
        previous_sequence=0,
        changed_pixels=50,
        changed_ratio=0.04,
        latency_ms=1.5,
        regions=(region,),
    )
    rois_active = processor.extract_rois(frame, with_change)
    assert len(rois_active) == 1
    assert rois_active[0].data.shape == (20, 20, 4)
    saved_ratio = processor.compute_work_saved_ratio(frame, rois_active)
    assert saved_ratio >= 95.0


# ── Frame Change Processor Tests ─────────────────────────────────────────────

def test_processor_requires_two_frames() -> None:
    buffer = FrameBuffer(max_size=4)
    processor = FrameChangeProcessor(OpenCVChangeDetector())

    assert processor.process_buffer(buffer) is None
    buffer.push(make_frame(1, np.full((32, 32, 4), 0, dtype=np.uint8)))
    assert processor.process_buffer(buffer) is None


def test_processor_skips_already_processed_latest_frame() -> None:
    buffer = FrameBuffer(max_size=4)
    buffer.push(make_frame(1, np.full((32, 32, 4), 0, dtype=np.uint8)))
    buffer.push(make_frame(2, np.full((32, 32, 4), 255, dtype=np.uint8)))
    processor = FrameChangeProcessor(
        OpenCVChangeDetector(ChangeDetectionConfig(threshold=10, min_area=1, blur_kernel=0))
    )

    assert processor.process_buffer(buffer) is not None
    assert processor.process_buffer(buffer) is None
    assert processor.metrics.snapshot().frames_processed == 1


# ── High Precision Perception Pipeline Tests ─────────────────────────────────

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


class FakePipelineRapidOCR:
    def __call__(self, image):
        return [[[[100, 100], [200, 100], [200, 130], [100, 130]], "Cancel", 0.90]], None


def test_high_precision_pipeline_merges_uia_and_ocr() -> None:
    frame1 = Frame(timestamp=1.0, width=300, height=200, data=np.zeros((200, 300, 4), dtype=np.uint8), sequence=1)
    frame2 = Frame(timestamp=1.1, width=300, height=200, data=np.full((200, 300, 4), 255, dtype=np.uint8), sequence=2)

    pipeline = HighPrecisionPerceptionPipeline(
        uia_inspector=FakeUIAInspector(),
        ocr_engine=RapidOCREngine(ocr_client=FakePipelineRapidOCR()),
    )

    analysis = pipeline.process_frame(current_frame=frame2, previous_frame=frame1)

    assert analysis.changed is True
    assert len(analysis.elements) == 2
    assert analysis.elements[0].text == "Submit"
    assert analysis.elements[0].source == "uia"
    assert analysis.elements[1].text == "Cancel"
    assert analysis.elements[1].source == "ocr_rapid"
    assert analysis.errors == ()


# ── OCR Engine Tests ─────────────────────────────────────────────────────────

class FakePaddleOCR:
    def ocr(self, image, cls=False):
        assert image.shape == (20, 30, 3)
        return [[[[1, 2], [11, 2], [11, 8], [1, 8]], ("Guardar", 0.92)]]


class FakeRapidOCR:
    def __call__(self, image):
        assert image.shape == (20, 30, 3)
        return [[[[1, 2], [11, 2], [11, 8], [1, 8]], "Aceptar", 0.95]], None


def test_paddle_ocr_engine_parses_v2_result() -> None:
    frame = Frame(timestamp=1.0, width=30, height=20, data=np.zeros((20, 30, 4), dtype=np.uint8), sequence=1)
    engine = PaddleOCREngine(OCRConfig(min_confidence=0.5), ocr_client=FakePaddleOCR())

    result = engine.analyze(frame)

    assert result.text_count == 1
    assert result.elements[0].text == "Guardar"
    assert result.elements[0].bbox.to_tuple() == (1, 2, 11, 8)
    assert result.errors == ()


def test_rapid_ocr_engine_parses_result() -> None:
    frame = Frame(timestamp=1.0, width=30, height=20, data=np.zeros((20, 30, 4), dtype=np.uint8), sequence=1)
    engine = RapidOCREngine(OCRConfig(min_confidence=0.5), ocr_client=FakeRapidOCR())

    result = engine.analyze(frame)

    assert len(result.elements) == 1
    assert result.elements[0].text == "Aceptar"
    assert result.elements[0].bbox.to_tuple() == (1, 2, 11, 8)
    assert result.elements[0].source == "ocr_rapid"


def test_auto_ocr_engine_fallback() -> None:
    frame = Frame(timestamp=1.0, width=30, height=20, data=np.zeros((20, 30, 4), dtype=np.uint8), sequence=1)
    engine = AutoOCREngine(preferred_engine=DummyOCREngine())

    result = engine.analyze(frame)
    assert result.elements == ()
    assert result.errors == ()


# ── Vision Model Tests ───────────────────────────────────────────────────────

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
