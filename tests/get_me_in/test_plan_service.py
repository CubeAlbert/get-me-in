"""Tests for PlanService invariants and snapshot behavior."""

import unittest

from src.get_me_in.application.plan_service import PlanService
from src.get_me_in.domain.plans import Plan, PlanItem, PlanStatus


class PlanServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = PlanService(_Ids())

    def test_create_activates_only_the_first_item(self) -> None:
        plan = self.service.create(("first", "second"))

        self.assertEqual(
            (PlanStatus.IN_PROGRESS, PlanStatus.PENDING),
            tuple(item.status for item in plan.items),
        )

    def test_completion_activates_the_next_pending_item(self) -> None:
        plan = self.service.create(("first", "second"))

        updated = self.service.update_status(plan.items[0].item_id, PlanStatus.COMPLETED)

        self.assertEqual(PlanStatus.IN_PROGRESS, updated.items[1].status)

    def test_replan_preserves_completed_items(self) -> None:
        plan = self.service.create(("first", "second"))
        self.service.update_status(plan.items[0].item_id, PlanStatus.COMPLETED)

        replanned = self.service.replan(("replacement",))

        self.assertEqual("first", replanned.items[0].description)
        self.assertEqual(PlanStatus.COMPLETED, replanned.items[0].status)
        self.assertEqual(PlanStatus.IN_PROGRESS, replanned.items[1].status)

    def test_restore_rejects_multiple_active_items(self) -> None:
        with self.assertRaises(ValueError):
            self.service.restore(
                Plan(
                    "plan",
                    (
                        PlanItem("one", "one", PlanStatus.IN_PROGRESS),
                        PlanItem("two", "two", PlanStatus.IN_PROGRESS),
                    ),
                )
            )


class _Ids:
    def __init__(self) -> None:
        self._value = 0

    def new_id(self) -> str:
        self._value += 1
        return str(self._value)
