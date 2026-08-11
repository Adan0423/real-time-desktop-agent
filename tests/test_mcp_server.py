from __future__ import annotations

from rtda.capture.interface import MonitorInfo
from rtda.mcp import server
from rtda.mcp.server import build_mcp_server, capture_monitors, classify_action, dry_run_action, health, plan_goal


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
    server = build_mcp_server()

    assert server is not None


def test_mcp_capture_monitors_is_json_ready(monkeypatch) -> None:
    class FakeRuntime:
        def __init__(self, _config) -> None:
            pass

        def list_monitors(self):
            return [MonitorInfo(0, 123, 0, 0, 100, 80, True, "DISPLAY1")]

    monkeypatch.setattr(server, "RTDAComplementRuntime", FakeRuntime)

    payload = capture_monitors()

    assert payload["monitors"][0]["width"] == 100
