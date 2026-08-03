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
    ToolParameter,
    ToolPolicy,
    ToolSchema,
    ToolSuccess,
)


class PlanToolContext(ToolHandlerContext, Protocol):
    """Context required by the Plan tool handlers."""

    plan: PlanService | None


def build_plan_tools() -> tuple[ToolDefinition, ...]:
    """Build PlanService-backed tools without global agent context."""
    return (
        ToolDefinition(
            name="create_plan",
            purpose="创建一个结构化的执行计划，将复杂任务分解为有序步骤列表",
            use_when="满足以下任意情况：\n- 用户明确要求制定计划\n- 任务预计持续较长时间\n- 存在多个可以独立完成的子任务\n- 后续步骤可能因为前一步失败而调整\n- 用户需要持续看到执行进度",
            do_not_use_when="满足以下任意情况：\n- 任务只是一个连续的线性流程\n- 所有步骤都会连续执行且无需等待用户\n- 不需要跟踪执行状态\n- 不需要向用户展示进度\n- 预计可以一次回复完成",
            expected_output="返回创建后的完整计划状态，包括每个项的 id/描述/状态、当前激活项及是否全部完成",
            schema=ToolSchema(
                {
                    "items": ToolParameter(
                        list,
                        "计划项描述列表，每个字符串是一个步骤的简短描述",
                        items=str,
                    )
                },
                frozenset({"items"}),
            ),
            policy=ToolPolicy(frozenset({Capability.PLAN})),
            handler=_create_plan,
        ),
        ToolDefinition(
            name="update_plan_status",
            purpose="更新指定计划项的状态：完成、取消，或将待执行项标记为进行中",
            use_when="重要：每次计划步骤的状态发生任何变化（完成、取消、跳过、回退等）时，必须先调用本工具更新状态，再继续执行后续步骤。不更新状态会导致 LLM 丢失计划进度。\n典型场景：当前步骤完成 → completed；需要跳过某步骤 → cancelled；需要回退重做 → pending",
            do_not_use_when="计划不存在或所有项已完成时",
            expected_output="返回更新后的完整计划状态",
            schema=ToolSchema(
                {
                    "id": ToolParameter(str, "要更新的计划项 id"),
                    "status": ToolParameter(
                        str,
                        "新状态: pending / in_progress / completed / cancelled",
                        allowed_values=tuple(status.value for status in PlanStatus),
                    ),
                },
                frozenset({"id", "status"}),
            ),
            policy=ToolPolicy(frozenset({Capability.PLAN})),
            handler=_update_plan_status,
        ),
        ToolDefinition(
            name="cancel_all_plans",
            purpose="取消所有未完成的计划项，清空当前计划",
            use_when="用户明确要求取消当前计划，或计划已不再适用需要重新规划时",
            do_not_use_when="只想取消单个步骤时（应使用 update_plan_status）",
            expected_output="返回取消后的完整计划状态",
            schema=ToolSchema({}),
            policy=ToolPolicy(frozenset({Capability.PLAN})),
            handler=_cancel_all_plans,
        ),
        ToolDefinition(
            name="replan",
            purpose="当新的执行结果表明活动计划的未完成部分已经不再有效、完整、必要或可执行时，修订剩余计划。保留原始目标和已完成工作。",
            use_when="在获得工具结果或完成计划步骤后，如果至少一个未完成步骤需要被新增、删除、替换、重新排序、拆分、合并或修改依赖关系，应主动调用此工具。\n典型触发条件包括：步骤被阻塞、原始假设失效、约束发生变化、缺少必要步骤、部分步骤变得多余、所需资源不可用、执行策略失败，或用户在不改变总体目标的情况下修改了要求。\n如果继续执行当前计划可能导致失败、错误结果或明显的无效工作，应先调用此工具，再继续执行。",
            do_not_use_when="当前没有活动计划、原始目标应被取消、只是更新步骤状态、剩余计划仍然有效，或者失败步骤可以直接重试且不影响后续步骤时，不要调用此工具。\n不要因为步骤失败本身而重新规划。只有当失败或新信息要求修改剩余计划结构时，才调用 replan。",
            expected_output="返回新计划状态，保留已完成项，未完成项被替换为新步骤列表，首项自动激活为 in_progress",
            schema=ToolSchema(
                {
                    "items": ToolParameter(
                        list,
                        "新的计划步骤描述列表，替代当前所有未完成项（已完成项保留）",
                        items=str,
                    )
                },
                frozenset({"items"}),
            ),
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
