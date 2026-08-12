from __future__ import annotations

import asyncio
import json
import time
from typing import Any, AsyncGenerator

from rtda.events.bus import DesktopEvent
from rtda.models.actions import ActionCommand, ActionType
from rtda.session.desktop_session import DesktopSession

# Fallback-safe import for FastAPI and WebSockets
try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.responses import JSONResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


class WebSocketConnectionManager:
    """Manages active WebSocket connections for event streaming."""

    def __init__(self) -> None:
        self.active_connections: list[Any] = []

    async def connect(self, websocket: Any) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: Any) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)
        for dead in dead_connections:
            self.disconnect(dead)


def create_service_app(session: DesktopSession | None = None) -> Any:
    """Factory creating the FastAPI Service Gateway application."""
    if not FASTAPI_AVAILABLE:
        raise RuntimeError("fastapi and uvicorn are required for the RTDA Service Gateway")

    app = FastAPI(
        title="Real-Time Desktop Agent (RTDA) Service Gateway",
        version="0.1.0",
        description="Administrative REST API & WebSocket Event Stream for RTDA Runtime v3",
    )

    active_session = session or DesktopSession()
    if not active_session.is_active:
        active_session.start()

    ws_manager = WebSocketConnectionManager()

    # Forward EventBus events to WebSocket clients
    def on_desktop_event(evt: DesktopEvent) -> None:
        payload = {
            "event": evt.name,
            "timestamp": evt.timestamp,
            "data": evt.data,
        }
        # Schedule broadcast on the event loop if running
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(ws_manager.broadcast(payload))
        except RuntimeError:
            pass

    active_session.event_bus.subscribe("*", on_desktop_event)

    # ── REST Routes ─────────────────────────────────────────────────────────

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {
            "name": "real-time-desktop-agent",
            "status": "ok",
            "uptime_seconds": round(time.time() - active_session._start_time, 1),
            "session_active": active_session.is_active,
            "session_id": active_session.session_id,
        }

    @app.get("/metrics")
    async def metrics() -> dict[str, Any]:
        current = active_session.state_store.get()
        return {
            "session_id": active_session.session_id,
            "focused_window": current.focused_window,
            "application": current.application,
            "element_count": len(current.elements),
            "uia_latency_ms": current.uia_snapshot.latency_ms if current.uia_snapshot else None,
            "last_action_latency_ms": current.last_action.latency_ms if current.last_action else None,
        }

    @app.get("/sessions")
    async def get_session() -> dict[str, Any]:
        return active_session.get_summary()

    @app.post("/sessions")
    async def restart_session() -> dict[str, Any]:
        active_session.stop()
        active_session.start()
        return {"message": "session restarted", "session_id": active_session.session_id}

    # ── WebSocket Streaming Routes ──────────────────────────────────────────

    @app.websocket("/events")
    async def websocket_events(websocket: WebSocket) -> None:
        """WebSocket endpoint streaming real-time desktop events to AI clients."""
        await ws_manager.connect(websocket)
        try:
            while True:
                # Keepalive ping/pong
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket)

    @app.websocket("/desktop")
    async def websocket_desktop_control(websocket: WebSocket) -> None:
        """Bidirectional Data Channel WebSocket: send command JSON, receive response JSON."""
        await websocket.accept()
        try:
            while True:
                raw_text = await websocket.receive_text()
                try:
                    payload = json.loads(raw_text)
                    action_type = payload.get("action")
                    target = payload.get("target")
                    value = payload.get("value")
                    dry_run = payload.get("dry_run", True)

                    if action_type == "observe":
                        state = active_session.observe()
                        await websocket.send_json({
                            "status": "ok",
                            "focused_window": state.focused_window,
                            "application": state.application,
                            "element_count": len(state.elements),
                        })
                    else:
                        res = active_session.execute_action(
                            action=action_type,
                            target=target,
                            value=value,
                            dry_run=dry_run,
                        )
                        await websocket.send_json(res.model_dump(mode="json"))
                except Exception as exc:
                    await websocket.send_json({"status": "error", "message": str(exc)})
        except WebSocketDisconnect:
            pass

    return app
