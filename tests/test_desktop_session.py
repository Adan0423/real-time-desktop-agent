from __future__ import annotations

from rtda.session.desktop_session import DesktopSession


def test_desktop_session_lifecycle() -> None:
    session = DesktopSession(dry_run_by_default=True)
    assert session.is_active is False

    session.start()
    assert session.is_active is True

    summary = session.get_summary()
    assert summary["is_active"] is True
    assert summary["session_id"] == session.session_id

    # Test observe
    state = session.observe()
    assert state is not None

    # Test execute action
    res = session.execute_action("click", target="OK")
    assert res.status.value in ("dry_run", "success")

    session.stop()
    assert session.is_active is False
