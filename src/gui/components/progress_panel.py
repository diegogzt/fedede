from __future__ import annotations

from enum import Enum


class ProgressState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class ProgressPanel:
    pass
