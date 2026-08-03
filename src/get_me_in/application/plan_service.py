"""Instance-scoped plan operations independent of agents and tools."""

from collections.abc import Iterable

from src.get_me_in.domain.plans import Plan, PlanItem, PlanStatus
from src.get_me_in.ports.ids import IdGenerator


class PlanService:
    """Maintains at most one in-progress item in its current plan."""

    def __init__(self, id_generator: IdGenerator) -> None:
        self._id_generator = id_generator
        self._plan: Plan | None = None

    def create(self, descriptions: Iterable[str]) -> Plan:
        values = tuple(item.strip() for item in descriptions)
        if not values or any(not item for item in values):
            raise ValueError("Plan requires one or more non-empty item descriptions")
        self._plan = Plan(
            plan_id=self._id_generator.new_id(),
            items=tuple(
                PlanItem(
                    item_id=self._id_generator.new_id(),
                    description=description,
                    status=PlanStatus.IN_PROGRESS if index == 0 else PlanStatus.PENDING,
                )
                for index, description in enumerate(values)
            ),
        )
        return self._plan

    def update_status(self, item_id: str, status: PlanStatus) -> Plan:
        plan = self._require_plan()
        matched = False
        items: list[PlanItem] = []
        for item in plan.items:
            if item.item_id == item_id:
                matched = True
                items.append(PlanItem(item.item_id, item.description, status))
            else:
                items.append(item)
        if not matched:
            raise KeyError(item_id)
        self._plan = self._normalize(Plan(plan.plan_id, tuple(items)))
        return self._plan

    def cancel_all(self) -> Plan:
        plan = self._require_plan()
        self._plan = Plan(
            plan.plan_id,
            tuple(
                PlanItem(item.item_id, item.description, PlanStatus.CANCELLED)
                if item.status in (PlanStatus.PENDING, PlanStatus.IN_PROGRESS)
                else item
                for item in plan.items
            ),
        )
        return self._plan

    def replan(self, descriptions: Iterable[str]) -> Plan:
        plan = self._require_plan()
        values = tuple(item.strip() for item in descriptions)
        if any(not item for item in values):
            raise ValueError("Plan items must not be blank")
        completed = tuple(item for item in plan.items if item.status is PlanStatus.COMPLETED)
        replacements = tuple(
            PlanItem(
                item_id=self._id_generator.new_id(),
                description=description,
                status=PlanStatus.IN_PROGRESS if index == 0 else PlanStatus.PENDING,
            )
            for index, description in enumerate(values)
        )
        self._plan = Plan(plan.plan_id, (*completed, *replacements))
        return self._plan

    def snapshot(self) -> Plan | None:
        return self._plan

    def restore(self, plan: Plan | None) -> None:
        self._plan = None if plan is None else self._normalize(plan)

    @staticmethod
    def _normalize(plan: Plan) -> Plan:
        active = [item for item in plan.items if item.status is PlanStatus.IN_PROGRESS]
        if len(active) > 1:
            raise ValueError("Plan cannot have more than one in-progress item")
        if active:
            return plan
        for index, item in enumerate(plan.items):
            if item.status is PlanStatus.PENDING:
                items = list(plan.items)
                items[index] = PlanItem(item.item_id, item.description, PlanStatus.IN_PROGRESS)
                return Plan(plan.plan_id, tuple(items))
        return plan

    def _require_plan(self) -> Plan:
        if self._plan is None:
            raise RuntimeError("No active plan")
        return self._plan
