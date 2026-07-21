"""Immutable plan models with a single active item invariant."""

from dataclasses import dataclass
from enum import StrEnum


class PlanStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class PlanItem:
    item_id: str
    description: str
    status: PlanStatus


@dataclass(frozen=True)
class Plan:
    plan_id: str
    items: tuple[PlanItem, ...]
