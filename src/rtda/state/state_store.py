from __future__ import annotations

from threading import Lock

from rtda.models.state import UIState


class StateStore:
    def __init__(self, initial: UIState | None = None) -> None:
        self._lock = Lock()
        self._state = initial or UIState()

    def get(self) -> UIState:
        with self._lock:
            return self._state

    def set(self, state: UIState) -> UIState:
        with self._lock:
            self._state = state
            return self._state
