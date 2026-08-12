from __future__ import annotations

from rtda.events.bus import (
    ActionExecutedEvent,
    DesktopEvent,
    EventBus,
    WindowChangedEvent,
)


def test_event_bus_subscribe_and_publish() -> None:
    bus = EventBus()
    received: list[DesktopEvent] = []

    def handler(evt: DesktopEvent) -> None:
        received.append(evt)

    bus.subscribe("window_changed", handler)

    evt1 = WindowChangedEvent(previous_window="App A", new_window="App B")
    bus.publish(evt1)

    assert len(received) == 1
    assert received[0].name == "window_changed"
    assert received[0].data["new_window"] == "App B"


def test_event_bus_global_subscriber() -> None:
    bus = EventBus()
    received: list[DesktopEvent] = []

    bus.subscribe("*", lambda evt: received.append(evt))

    bus.publish(WindowChangedEvent(previous_window=None, new_window="Notepad"))
    bus.publish(ActionExecutedEvent(action="click", target="Save", status="success", latency_ms=12.5))

    assert len(received) == 2
    assert received[0].name == "window_changed"
    assert received[1].name == "action_executed"
