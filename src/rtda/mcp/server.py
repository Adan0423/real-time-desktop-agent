from __future__ import annotations

import argparse
from dataclasses import asdict
from typing import Any

from rtda.actions.engine import ActionEngine
from rtda.actions.pyautogui_executor import PyAutoGUIActionExecutor
from rtda.agent.planner import RuleBasedPlanner
from rtda.models.actions import ActionCommand, ActionType
from rtda.models.state import UIState
from rtda.perception.uia import UIAConfig, WindowsUIAutomationInspector, summarize_uia_elements
from rtda.safety.action_guard import ActionGuard
from rtda.safety.confirmation import ConfirmationManager
from rtda.safety.policy import ActionPolicy


def health() -> dict[str, Any]:
    return {"name": "real-time-desktop-agent", "status": "ok", "phases": [1, 2, 3, 4, 5, 6, 7, 8]}


def inspect_uia(window_title: str | None = None, max_depth: int = 3, max_elements: int = 120) -> dict[str, Any]:
    inspector = WindowsUIAutomationInspector(UIAConfig(max_depth=max_depth, max_elements=max_elements))
    snapshot = inspector.snapshot(window_title=window_title)
    return {
        "element_count": snapshot.element_count,
        "latency_ms": snapshot.latency_ms,
        "truncated": snapshot.truncated,
        "errors": list(snapshot.errors),
        "elements": summarize_uia_elements(snapshot.elements),
    }


def plan_goal(goal: str) -> dict[str, Any]:
    plan = RuleBasedPlanner().plan(UIState(), goal)
    return {
        "goal": plan.goal,
        "rationale": plan.rationale,
        "actions": [action.model_dump(mode="json") for action in plan.actions],
    }


def classify_action(action: str, target: str | None = None, value: str | None = None) -> dict[str, Any]:
    command = ActionCommand(action=ActionType(action), target=target, value=value)
    guard = ActionGuard(policy=ActionPolicy(), confirmations=ConfirmationManager())
    allowed, risk, message = guard.allowed(command)
    return {"allowed": allowed, "risk": risk.value, "message": message}


def dry_run_action(action: str, target: str | None = None, value: str | None = None) -> dict[str, Any]:
    command = ActionCommand(action=ActionType(action), target=target, value=value)
    engine = ActionEngine(executor=PyAutoGUIActionExecutor(dry_run=True))
    result = engine.execute(command)
    return result.model_dump(mode="json")


def build_mcp_server():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError("mcp>=1.27,<2 is required to run the RTDA MCP server") from exc

    mcp = FastMCP("RTDA", json_response=True)
    mcp.tool()(health)
    mcp.tool()(inspect_uia)
    mcp.tool()(plan_goal)
    mcp.tool()(classify_action)
    mcp.tool()(dry_run_action)
    return mcp


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="RTDA MCP server")
    parser.add_argument("--transport", choices=["stdio", "streamable-http", "sse"], default="stdio")
    args = parser.parse_args(argv)
    server = build_mcp_server()
    server.run(transport=args.transport)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
