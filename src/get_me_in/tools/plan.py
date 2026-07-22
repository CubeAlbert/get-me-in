"""Plan tool definitions backed by the instance-scoped PlanService."""

from collections.abc import Mapping
from typing import Protocol

from src.get_me_in.application.plan_service import PlanService
from src.get_me_in.domain.plans import Plan, PlanStatus
from src.get_me_in.domain.agents import Capability
from src.get_me_in.domain.tools import (
    ToolDefinition,
    ToolFailure,
    ToolHandlerContext,
    ToolPolicy,
    ToolSchema,
    ToolSuccess,
)


class PlanToolContext(ToolHandlerContext, Protocol):
    """Context required by the v2 Plan tool handlers."""

    plan: PlanService | None


def build_plan_tools() -> tuple[ToolDefinition, ...]:
    """Build PlanService-backed tools without global agent context."""
    return (
        ToolDefinition(
            name="create_plan",
            description="创建有序执行计划，首项自动进入进行中状态。",
            schema=ToolSchema({"items": list}, frozenset({"items"})),
            policy=ToolPolicy(frozenset({Capability.PLAN})),
            handler=_create_plan,
        ),
        ToolDefinition(
            name="update_plan_status",
            description="更新计划项状态；完成或取消当前项时自动激活下一项。",
            schema=ToolSchema(
                {"id": str, "status": str},
                frozenset({"id", "status"}),
            ),
            policy=ToolPolicy(frozenset({Capability.PLAN})),
            handler=_update_plan_status,
        ),
        ToolDefinition(
            name="cancel_all_plans",
            description="取消当前计划中全部未完成项。",
            schema=ToolSchema({}),
            policy=ToolPolicy(frozenset({Capability.PLAN})),
            handler=_cancel_all_plans,
        ),
        ToolDefinition(
            name="replan",
            description="保留已完成项，并以新的步骤替换未完成项。",
            schema=ToolSchema({"items": list}, frozenset({"items"})),
            policy=ToolPolicy(frozenset({Capability.PLAN})),
            handler=_replan,
        ),
    )


def _create_plan(arguments: Mapping[str, object], context: PlanToolContext) -> ToolSuccess | ToolFailure:
    service = _plan_service(context)
    if isinstance(service, ToolFailure):
        return service
    try:
        return ToolSuccess(_plan_payload(service.create(arguments["items"])))
    except ValueError as error:
        return ToolFailure("invalid_plan", str(error))


def _update_plan_status(
    arguments: Mapping[str, object], context: PlanToolContext
) -> ToolSuccess | ToolFailure:
    service = _plan_service(context)
    if isinstance(service, ToolFailure):
        return service
    try:
        status = PlanStatus(arguments["status"])
    except ValueError:
        return ToolFailure("invalid_plan_status", f"Unknown plan status: {arguments['status']}")
    try:
        return ToolSuccess(_plan_payload(service.update_status(arguments["id"], status)))
    except KeyError:
        return ToolFailure("plan_item_not_found", f"Unknown plan item: {arguments['id']}")
    except RuntimeError as error:
        return ToolFailure("plan_unavailable", str(error))


def _cancel_all_plans(
    arguments: Mapping[str, object], context: PlanToolContext
) -> ToolSuccess | ToolFailure:
    del arguments
    service = _plan_service(context)
    if isinstance(service, ToolFailure):
        return service
    try:
        return ToolSuccess(_plan_payload(service.cancel_all()))
    except RuntimeError as error:
        return ToolFailure("plan_unavailable", str(error))


def _replan(arguments: Mapping[str, object], context: PlanToolContext) -> ToolSuccess | ToolFailure:
    service = _plan_service(context)
    if isinstance(service, ToolFailure):
        return service
    try:
        return ToolSuccess(_plan_payload(service.replan(arguments["items"])))
    except (RuntimeError, ValueError) as error:
        return ToolFailure("invalid_plan", str(error))


def _plan_service(context: PlanToolContext) -> PlanService | ToolFailure:
    if context.plan is None:
        return ToolFailure("plan_unavailable", "This tool requires a configured PlanService")
    return context.plan


def _plan_payload(plan: Plan) -> dict[str, object]:
    return {
        "id": plan.plan_id,
        "items": tuple(
            {"id": item.item_id, "description": item.description, "status": item.status.value}
            for item in plan.items
        ),
    }
