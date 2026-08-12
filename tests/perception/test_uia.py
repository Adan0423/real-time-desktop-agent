from __future__ import annotations

from rtda.models.perception import BoundingBox
from rtda.perception.uia import UIAConfig, WindowsUIAutomationInspector, summarize_uia_elements


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
