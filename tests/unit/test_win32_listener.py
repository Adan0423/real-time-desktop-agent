from __future__ import annotations

import time
from rtda.events.bus import EventBus, DesktopEvent
from rtda.events.win32_listener import Win32EventListener, UIObjectChangedEvent


def test_win32_listener_lifecycle() -> None:
    bus = EventBus()
    listener = Win32EventListener(event_bus=bus)

    received: list[DesktopEvent] = []
    bus.subscribe("*", lambda evt: received.append(evt))

    listener.start()
    time.sleep(0.1)
    assert listener._running is True

    # Publish dummy UIObjectChangedEvent to verify bus integration
    bus.publish(UIObjectChangedEvent(hwnd=12345, event_type="show"))
    assert len(received) == 1
    assert received[0].data["hwnd"] == 12345

    listener.stop()
    assert listener._running is False
