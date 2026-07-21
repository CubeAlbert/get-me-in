"""Validation and execution boundary for explicit v2 tools."""

from collections.abc import Mapping
from dataclasses import dataclass

from src.get_me_in.application.cancellation import CancellationToken
from src.get_me_in.application.plan_service import PlanService
from src.get_me_in.application.tool_catalog import ToolCatalog
from src.get_me_in.domain.agents import AgentKey, Capability
from src.get_me_in.domain.tools import (
    ConfirmationMode,
    ToolFailure,
    ToolInteraction,
    ToolOutcome,
)
from src.get_me_in.ports.workspace import WorkspacePort


@dataclass(frozen=True)
class ToolContext:
    """Per-call dependencies; R3 adds concrete Plan and Workspace services here."""

    session_id: str
    agent_key: AgentKey
    cancellation: CancellationToken
    plan: PlanService | None = None
    workspace: WorkspacePort | None = None
    approved: bool = False
    rejected: bool = False


class ToolExecutor:
    """Executes one ToolDefinition after deterministic boundary validation."""

    def __init__(self, catalog: ToolCatalog) -> None:
        self._catalog = catalog

    def execute(
        self,
        call_id: str,
        tool_name: str,
        arguments: Mapping[str, object],
        context: ToolContext,
        capabilities: frozenset[Capability] | None = None,
    ) -> ToolOutcome:
        del call_id
        if context.cancellation.is_cancelled:
            return ToolFailure("cancelled", "Tool call was cancelled before execution")
        if context.rejected:
            return ToolFailure("rejected", f"Tool call {tool_name} was rejected")
        try:
            definition = self._catalog.get(tool_name)
        except KeyError:
            return ToolFailure("unknown_tool", f"Unknown tool: {tool_name}")
        if capabilities is not None and not definition.policy.required_capabilities <= capabilities:
            return ToolFailure("tool_not_permitted", f"Tool {tool_name} is not available to this agent")
        if (
            definition.policy.confirmation is ConfirmationMode.ALWAYS
            and not context.approved
        ):
            return ToolInteraction(
                kind="approval",
                prompt=f"Approve tool {tool_name}?",
            )

        failure = self._validate_arguments(arguments, definition.schema.properties, definition.schema.required)
        if failure is not None:
            return failure
        try:
            return definition.handler(arguments, context)
        except Exception as error:
            return ToolFailure("tool_handler_error", str(error))

    @staticmethod
    def _validate_arguments(
        arguments: Mapping[str, object],
        properties: Mapping[str, type],
        required: frozenset[str],
    ) -> ToolFailure | None:
        missing = required - arguments.keys()
        if missing:
            return ToolFailure("missing_argument", f"Missing arguments: {', '.join(sorted(missing))}")
        unexpected = arguments.keys() - properties.keys()
        if unexpected:
            return ToolFailure("unexpected_argument", f"Unexpected arguments: {', '.join(sorted(unexpected))}")
        for name, value in arguments.items():
            expected_type = properties[name]
            if not isinstance(value, expected_type):
                return ToolFailure(
                    "invalid_argument_type",
                    f"Argument {name} must be {expected_type.__name__}",
                )
        return None
