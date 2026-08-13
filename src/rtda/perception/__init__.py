"""Perception pipeline primitives."""

from rtda.perception.change_detector import FrameChangeProcessor
from rtda.perception.high_precision_pipeline import HighPrecisionAnalysis, HighPrecisionPerceptionPipeline
from rtda.perception.interface import ChangeDetector, OCREngine, UIAutomationInspector, VisionModel
from rtda.perception.ocr import AutoOCREngine, DummyOCREngine, OCRConfig, PaddleOCREngine, RapidOCREngine
from rtda.perception.opencv_detector import ChangeDetectionConfig, OpenCVChangeDetector
from rtda.perception.uia import UIAConfig, WindowsUIAutomationInspector
from rtda.perception.vision_model import ONNXRuntimeVisionModel, ONNXVisionConfig, StructuredVisionModel

__all__ = [
    "AutoOCREngine",
    "ChangeDetectionConfig",
    "ChangeDetector",
    "DummyOCREngine",
    "FrameChangeProcessor",
    "HighPrecisionAnalysis",
    "HighPrecisionPerceptionPipeline",
    "OCRConfig",
    "OCREngine",
    "ONNXRuntimeVisionModel",
    "ONNXVisionConfig",
    "OpenCVChangeDetector",
    "PaddleOCREngine",
    "RapidOCREngine",
    "StructuredVisionModel",
    "UIAConfig",
    "UIAutomationInspector",
    "VisionModel",
    "WindowsUIAutomationInspector",
]

