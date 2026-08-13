from __future__ import annotations

import time
import pytest
from fastapi.testclient import TestClient

from rtda.actions.engine import ActionEngine
from rtda.actions.pyautogui_executor import PyAutoGUIActionExecutor
from rtda.actions.resolver import TargetResolver
from rtda.actions.win32_input import Win32SendInputBackend
from rtda.agent.executor import AgentExecutor
from rtda.capture.interface import MonitorInfo
from rtda.events.bus import ActionExecutedEvent, DesktopEvent, EventBus, WindowChangedEvent
from rtda.events.win32_listener import Win32EventListener, UIObjectChangedEvent
from rtda.mcp import server
from rtda.mcp.server import build_mcp_server, capture_monitors, classify_action, dry_run_action, health, plan_goal
from rtda.models.actions import ActionCommand, ActionRisk, ActionStatus, ActionType, ResolvedAction
from rtda.models.perception import BoundingBox, PerceptionElement
from rtda.models.state import UIState
from rtda.service.gateway import create_service_app
from rtda.session.desktop_session import DesktopSession
from rtda.state.state_machine import AgentPhase, StateMachine
from rtda.state.state_store import StateStore


# ── Action Engine & Win32 Input Tests ───────────────────────────────────────

def test_action_engine_resolves_semantic_target_in_dry_run() -> None:
    element = PerceptionElement(
        type="ButtonControl",
        text="Guardar",
        bbox=BoundingBox(10, 20, 30, 40),
        confidence=0.9,
        source="uia",
    )
    engine = ActionEngine(
        resolver=TargetResolver((element,)),
        executor=PyAutoGUIActionExecutor(dry_run=True),
    )

    result = engine.execute(ActionCommand(action=ActionType.CLICK, target="Guardar"))

    assert result.status == ActionStatus.DRY_RUN
    assert result.resolved_bbox == element.bbox
    assert result.metadata["x"] == 20
    assert result.metadata["y"] == 30


def test_action_engine_blocks_dangerous_action_without_confirmation() -> None:
    engine = ActionEngine()
    result = engine.execute(ActionCommand(action=ActionType.DELETE, target="file"))

    assert result.status == ActionStatus.BLOCKED
    assert "requires confirmation" in result.message


def test_win32_input_dry_run() -> None:
    backend = Win32SendInputBackend(dry_run=True)
    cmd = ActionCommand(action=ActionType.CLICK, target="Button")
    resolved = ResolvedAction(command=cmd, risk=ActionRisk.SAFE, x=100, y=200)

    res = backend.execute(resolved)
    assert res.status == ActionStatus.DRY_RUN
    assert res.metadata["backend"] == "win32_send_input"
    assert res.metadata["x"] == 100
    assert res.metadata["y"] == 200


# ── Agent Executor Tests ───────────────────────────────────────────────────

def test_agent_runs_one_action_then_verifies() -> None:
    state = UIState(
        elements=(
            PerceptionElement(
                type="ButtonControl",
                text="Guardar",
                bbox=BoundingBox(0, 0, 20, 20),
                confidence=1.0,
                source="uia",
            ),
        )
    )
    agent = AgentExecutor(
        state_store=StateStore(state),
        action_engine=ActionEngine(executor=PyAutoGUIActionExecutor(dry_run=True)),
    )

    result = agent.run_once("click Guardar")

    assert result.plan.actions
    assert result.action_results[0].status == "dry_run"
    assert result.verification is not None
    assert result.verification.success is True


# ── Desktop Session Tests ───────────────────────────────────────────────────

def test_desktop_session_lifecycle() -> None:
    session = DesktopSession(dry_run_by_default=True)
    assert session.is_active is False

    session.start()
    assert session.is_active is True

    summary = session.get_summary()
    assert summary["is_active"] is True
    assert summary["session_id"] == session.session_id

    state = session.observe()
    assert state is not None

    res = session.execute_action("click", target="OK")
    assert res.status.value in ("dry_run", "success")

    session.stop()
    assert session.is_active is False


# ── Event Bus & Win32 Listener Tests ───────────────────────────────────────

def test_event_bus_subscribe_and_publish() -> None:
    bus = EventBus()
    received: list[DesktopEvent] = []

    bus.subscribe("window_changed", lambda evt: received.append(evt))
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


def test_win32_listener_lifecycle() -> None:
    bus = EventBus()
    listener = Win32EventListener(event_bus=bus)

    received: list[DesktopEvent] = []
    bus.subscribe("*", lambda evt: received.append(evt))

    listener.start()
    time.sleep(0.1)
    assert listener._running is True

    bus.publish(UIObjectChangedEvent(hwnd=12345, event_type="show"))
    assert len(received) == 1
    assert received[0].data["hwnd"] == 12345

    listener.stop()
    assert listener._running is False


# ── State Machine Tests ─────────────────────────────────────────────────────

def test_state_machine_rejects_invalid_transition() -> None:
    machine = StateMachine()

    with pytest.raises(ValueError):
        machine.transition(AgentPhase.ACT)


# ── MCP Server Tests ────────────────────────────────────────────────────────

def test_mcp_health_and_plan_tools_are_json_ready() -> None:
    assert health()["status"] == "ok"
    plan = plan_goal("click Guardar")

    assert plan["actions"][0]["action"] == "click"


def test_mcp_classify_and_dry_run_action() -> None:
    blocked = classify_action("delete", target="file")
    dry_run = dry_run_action("click", target="Guardar")

    assert blocked["allowed"] is False
    assert dry_run["status"] == "dry_run"


def test_mcp_server_builds() -> None:
    srv = build_mcp_server()
    assert srv is not None


def test_mcp_capture_monitors_is_json_ready(monkeypatch) -> None:
    class FakeRuntime:
        def __init__(self, _config) -> None:
            pass

        def list_monitors(self):
            return [MonitorInfo(0, 123, 0, 0, 100, 80, True, "DISPLAY1")]

    monkeypatch.setattr(server, "RTDAComplementRuntime", FakeRuntime)
    payload = capture_monitors()

    assert payload["monitors"][0]["width"] == 100


# ── Service Gateway REST & WebSocket Tests ──────────────────────────────────

def test_service_gateway_rest_routes() -> None:
    session = DesktopSession(dry_run_by_default=True)
    session.start()

    app = create_service_app(session=session)
    client = TestClient(app)

    res_health = client.get("/health")
    assert res_health.status_code == 200
    data_health = res_health.json()
    assert data_health["status"] == "ok"
    assert data_health["session_active"] is True
    assert data_health["session_id"] == session.session_id

    res_metrics = client.get("/metrics")
    assert res_metrics.status_code == 200
    data_metrics = res_metrics.json()
    assert "focused_window" in data_metrics
    assert "element_count" in data_metrics

    res_session = client.get("/sessions")
    assert res_session.status_code == 200
    data_session = res_session.json()
    assert data_session["session_id"] == session.session_id


def test_service_gateway_websocket_desktop_control() -> None:
    session = DesktopSession(dry_run_by_default=True)
    session.start()

    app = create_service_app(session=session)
    client = TestClient(app)

    with client.websocket_connect("/desktop") as websocket:
        websocket.send_json({"action": "observe"})
        data = websocket.receive_json()
        assert data["status"] == "ok"
        assert "focused_window" in data

        websocket.send_json({"action": "click", "target": "Save", "dry_run": True})
        res_action = websocket.receive_json()
        assert res_action["status"] in ("dry_run", "success")
