from __future__ import annotations

import time
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from rtda.models.perception import BoundingBox


class ActionRisk(StrEnum):
    SAFE = "safe"
    MODERATE = "moderate"
    DANGEROUS = "dangerous"


class ActionStatus(StrEnum):
    PENDING = "pending"
    SUCCESS = "success"
    BLOCKED = "blocked"
    FAILED = "failed"
    DRY_RUN = "dry_run"


class ActionType(StrEnum):
    MOVE = "move"
    HOVER = "hover"
    CLICK = "click"
    TYPE = "type"
    PRESS = "press"
    HOTKEY = "hotkey"
    SCROLL = "scroll"
    READ = "read"
    INSPECT = "inspect"
    NAVIGATE = "navigate"
    DELETE = "delete"
    PUBLISH = "publish"
    SEND = "send"
    PURCHASE = "purchase"
    SUBMIT = "submit"


class ActionCommand(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    action: ActionType
    target: str | None = None
    value: str | None = None
    keys: list[str] = Field(default_factory=list)
    amount: int | None = None
    bbox: BoundingBox | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResolvedAction(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    command: ActionCommand
    risk: ActionRisk
    x: int | None = None
    y: int | None = None
    bbox: BoundingBox | None = None
    resolved_by: str | None = None


class ActionResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    command: ActionCommand
    status: ActionStatus
    risk: ActionRisk
    message: str
    latency_ms: float = 0.0
    resolved_bbox: BoundingBox | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)
