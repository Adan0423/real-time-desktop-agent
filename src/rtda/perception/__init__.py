"""Perception pipeline primitives."""

from rtda.perception.change_detector import FrameChangeProcessor
from rtda.perception.interface import ChangeDetector, OCREngine, UIAutomationInspector, VisionModel
from rtda.perception.ocr import OCRConfig, PaddleOCREngine
from rtda.perception.opencv_detector import ChangeDetectionConfig, OpenCVChangeDetector
from rtda.perception.uia import UIAConfig, WindowsUIAutomationInspector
from rtda.perception.vision_model import ONNXRuntimeVisionModel, ONNXVisionConfig, StructuredVisionModel

__all__ = [
    "ChangeDetectionConfig",
    "ChangeDetector",
    "FrameChangeProcessor",
    "OCRConfig",
    "OCREngine",
    "ONNXRuntimeVisionModel",
    "ONNXVisionConfig",
    "OpenCVChangeDetector",
    "PaddleOCREngine",
    "StructuredVisionModel",
    "UIAConfig",
    "UIAutomationInspector",
    "VisionModel",
    "WindowsUIAutomationInspector",
]
