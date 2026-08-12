from __future__ import annotations

from fastapi.testclient import TestClient

from rtda.service.gateway import create_service_app
from rtda.session.desktop_session import DesktopSession


def test_service_gateway_rest_routes() -> None:
    session = DesktopSession(dry_run_by_default=True)
    session.start()

    app = create_service_app(session=session)
    client = TestClient(app)

    # Test /health
    res_health = client.get("/health")
    assert res_health.status_code == 200
    data_health = res_health.json()
    assert data_health["status"] == "ok"
    assert data_health["session_active"] is True
    assert data_health["session_id"] == session.session_id

    # Test /metrics
    res_metrics = client.get("/metrics")
    assert res_metrics.status_code == 200
    data_metrics = res_metrics.json()
    assert "focused_window" in data_metrics
    assert "element_count" in data_metrics

    # Test /sessions
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
        # Send observe command
        websocket.send_json({"action": "observe"})
        data = websocket.receive_json()
        assert data["status"] == "ok"
        assert "focused_window" in data

        # Send click command (dry_run)
        websocket.send_json({"action": "click", "target": "Save", "dry_run": True})
        res_action = websocket.receive_json()
        assert res_action["status"] in ("dry_run", "success")
