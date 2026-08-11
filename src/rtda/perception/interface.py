from __future__ import annotations

from abc import ABC, abstractmethod

from rtda.capture.frame import Frame
from rtda.models.perception import ChangeDetectionResult, OCRResult, UIASnapshot, VisionAnalysis, VisionLocateResult


class ChangeDetector(ABC):
    @abstractmethod
    def detect(self, previous: Frame, current: Frame) -> ChangeDetectionResult:
        raise NotImplementedError


class UIAutomationInspector(ABC):
    @abstractmethod
    def snapshot(self, *, window_title: str | None = None) -> UIASnapshot:
        raise NotImplementedError


class OCREngine(ABC):
    @abstractmethod
    def analyze(self, frame: Frame) -> OCRResult:
        raise NotImplementedError


class VisionModel(ABC):
    @abstractmethod
    async def analyze(self, frame: Frame, instruction: str) -> VisionAnalysis:
        raise NotImplementedError

    @abstractmethod
    async def locate(self, frame: Frame, target: str) -> VisionLocateResult:
        raise NotImplementedError
