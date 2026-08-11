from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Iterable

from rtda.models.perception import BoundingBox, UIAElement, UIASnapshot
from rtda.perception.interface import UIAutomationInspector


@dataclass(frozen=True, slots=True)
class UIAConfig:
    max_depth: int = 4
    max_elements: int = 300
    include_offscreen: bool = False
    include_empty_names: bool = False
    exclude_outside_root: bool = True
    outside_root_margin: int = 64
    search_timeout_s: float = 1.0

    def __post_init__(self) -> None:
        if self.max_depth < 0:
            raise ValueError("max_depth must be non-negative")
        if self.max_elements <= 0:
            raise ValueError("max_elements must be positive")
        if self.search_timeout_s < 0:
            raise ValueError("search_timeout_s must be non-negative")
        if self.outside_root_margin < 0:
            raise ValueError("outside_root_margin must be non-negative")


class WindowsUIAutomationInspector(UIAutomationInspector):
    """Read-only Windows UI Automation tree inspector."""

    def __init__(self, config: UIAConfig | None = None) -> None:
        self.config = config or UIAConfig()

    def snapshot(self, *, window_title: str | None = None) -> UIASnapshot:
        started = time.perf_counter()
        errors: list[str] = []
        elements: list[UIAElement] = []
        root_element: UIAElement | None = None
        root_bbox: BoundingBox | None = None
        truncated = False

        try:
            root_control = self._resolve_root(window_title)
        except Exception as exc:
            latency_ms = (time.perf_counter() - started) * 1000.0
            return UIASnapshot(
                timestamp=time.time(),
                latency_ms=latency_ms,
                elements=(),
                window_title=window_title,
                errors=(f"resolve_root: {type(exc).__name__}: {exc}",),
            )

        stack: list[tuple[Any, int, str]] = [(root_control, 0, "0")]
        while stack:
            control, depth, path = stack.pop()
            if len(elements) >= self.config.max_elements:
                truncated = True
                break

            children: tuple[Any, ...] = ()
            if depth < self.config.max_depth:
                try:
                    children = tuple(control.GetChildren())
                except Exception as exc:
                    errors.append(f"{path}.children: {type(exc).__name__}: {exc}")

            try:
                element = self._control_to_element(control, depth=depth, path=path, child_count=len(children))
            except Exception as exc:
                errors.append(f"{path}: {type(exc).__name__}: {exc}")
                continue

            if depth == 0:
                root_element = element
                root_bbox = element.bbox
            if self._should_include(element, root_bbox=root_bbox):
                elements.append(element)

            if depth >= self.config.max_depth:
                continue
            for index, child in reversed(list(enumerate(children))):
                stack.append((child, depth + 1, f"{path}.{index}"))

        latency_ms = (time.perf_counter() - started) * 1000.0
        return UIASnapshot(
            timestamp=time.time(),
            latency_ms=latency_ms,
            root=root_element,
            elements=tuple(elements),
            window_title=window_title,
            truncated=truncated,
            errors=tuple(errors),
        )

    def _resolve_root(self, window_title: str | None) -> Any:
        import uiautomation as auto

        root = auto.GetRootControl()
        if not window_title:
            return root

        deadline = time.perf_counter() + self.config.search_timeout_s
        window_title_lower = window_title.casefold()
        while True:
            for child in root.GetChildren():
                name = self._safe_get(child, "Name", "") or ""
                if window_title_lower in name.casefold():
                    return child
            if time.perf_counter() >= deadline:
                raise LookupError(f"window title not found: {window_title}")
            time.sleep(0.05)

    def _control_to_element(self, control: Any, *, depth: int, path: str, child_count: int = 0) -> UIAElement:
        return UIAElement(
            name=str(self._safe_get(control, "Name", "") or ""),
            control_type=str(self._safe_get(control, "ControlTypeName", "") or "UnknownControl"),
            bbox=self._bbox_from_rect(self._safe_get(control, "BoundingRectangle", None)),
            enabled=self._safe_bool(self._safe_get(control, "IsEnabled", None)),
            offscreen=self._safe_bool(self._safe_get(control, "IsOffscreen", None)),
            automation_id=self._safe_str(self._safe_get(control, "AutomationId", None)),
            class_name=self._safe_str(self._safe_get(control, "ClassName", None)),
            process_id=self._safe_int(self._safe_get(control, "ProcessId", None)),
            native_window_handle=self._safe_int(self._safe_get(control, "NativeWindowHandle", None)),
            depth=depth,
            path=path,
            child_count=child_count,
        )

    def _should_include(self, element: UIAElement, *, root_bbox: BoundingBox | None) -> bool:
        if not self.config.include_offscreen and element.offscreen:
            return False
        if not self.config.include_empty_names and not element.name and element.bbox is None:
            return False
        if (
            self.config.exclude_outside_root
            and root_bbox is not None
            and element.depth > 0
            and element.bbox is not None
            and not self._intersects_with_margin(element.bbox, root_bbox, self.config.outside_root_margin)
        ):
            return False
        return True

    @staticmethod
    def _intersects_with_margin(bbox: BoundingBox, root: BoundingBox, margin: int) -> bool:
        expanded = BoundingBox(
            left=root.left - margin,
            top=root.top - margin,
            right=root.right + margin,
            bottom=root.bottom + margin,
        )
        return bbox.intersects(expanded)

    @staticmethod
    def _safe_get(control: Any, name: str, default: Any) -> Any:
        try:
            return getattr(control, name)
        except Exception:
            return default

    @staticmethod
    def _safe_bool(value: Any) -> bool | None:
        return None if value is None else bool(value)

    @staticmethod
    def _safe_int(value: Any) -> int | None:
        try:
            return None if value is None else int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_str(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value)
        return text or None

    @staticmethod
    def _bbox_from_rect(rect: Any) -> BoundingBox | None:
        if rect is None:
            return None
        try:
            left = int(rect.left)
            top = int(rect.top)
            right = int(rect.right)
            bottom = int(rect.bottom)
        except Exception:
            return None
        if right <= left or bottom <= top:
            return None
        return BoundingBox(left=left, top=top, right=right, bottom=bottom)


def summarize_uia_elements(elements: Iterable[UIAElement], *, limit: int = 20) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for element in list(elements)[:limit]:
        rows.append(
            {
                "path": element.path,
                "depth": element.depth,
                "type": element.control_type,
                "name": element.name,
                "bbox": element.bbox.to_tuple() if element.bbox else None,
                "enabled": element.enabled,
                "offscreen": element.offscreen,
                "automation_id": element.automation_id,
                "class_name": element.class_name,
            }
        )
    return rows
