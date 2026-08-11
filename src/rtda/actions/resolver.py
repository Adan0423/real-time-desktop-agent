from __future__ import annotations

from dataclasses import dataclass

from rtda.models.actions import ActionCommand, ActionRisk, ResolvedAction
from rtda.models.perception import BoundingBox, PerceptionElement


@dataclass(slots=True)
class TargetResolver:
    elements: tuple[PerceptionElement, ...] = ()

    def update(self, elements: tuple[PerceptionElement, ...]) -> None:
        self.elements = elements

    def resolve(self, command: ActionCommand, risk: ActionRisk) -> ResolvedAction:
        bbox = command.bbox or self._find_bbox(command.target)
        x: int | None = None
        y: int | None = None
        if bbox is not None:
            x = bbox.left + bbox.width // 2
            y = bbox.top + bbox.height // 2
        return ResolvedAction(
            command=command,
            risk=risk,
            x=x,
            y=y,
            bbox=bbox,
            resolved_by="explicit_bbox" if command.bbox else ("perception" if bbox else None),
        )

    def _find_bbox(self, target: str | None) -> BoundingBox | None:
        if not target:
            return None
        needle = target.casefold()
        matches = [
            element
            for element in self.elements
            if element.bbox is not None
            and ((element.text and needle in element.text.casefold()) or needle in element.type.casefold())
        ]
        if not matches:
            return None
        matches.sort(key=lambda element: element.confidence, reverse=True)
        return matches[0].bbox
