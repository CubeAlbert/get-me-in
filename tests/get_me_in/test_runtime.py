"""Tests for the pull-driven typed agent runtime."""

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from src.get_me_in.application.agent_catalog import AgentCatalog
from src.get_me_in.application.cancellation import CancellationToken
from src.get_me_in.application.commands import Approve, Cancel, Continue, Reject, SubmitSelection, UserMessage
from src.get_me_in.application.events import (
    ApprovalRequested,
    Cancelled,
    Completed,
    Failed,
    HandoffRequested,
    Progress,
    SelectionRequested,
    ToolFinished,
    ToolStarted,
)
from src.get_me_in.application.prompt_renderer import PromptRenderer
from src.get_me_in.application.plan_service import PlanService
from src.get_me_in.application.runtime import AgentRuntime
from src.get_me_in.application.tool_catalog import ToolCatalog
from src.get_me_in.application.tool_executor import ToolContext, ToolExecutor
from src.get_me_in.domain.agents import AgentKey, AgentSpec, AgentStyle, Capability
from src.get_me_in.domain.sessions import AgentSessionState
from src.get_me_in.domain.tools import ConfirmationMode, ToolDefinition, ToolPolicy, ToolSchema, ToolSuccess
from src.get_me_in.ports.llm import CancellationSignal, LLMRequest, LLMResult, ModelProfile
from src.get_me_in.tools.switch import build_switch_tools
from src.get_me_in.tools.plan import build_plan_tools


class RuntimeTests(unittest.TestCase):
    def test_user_message_completes_and_never_replays_thinking(self) -> None:
        runtime, llm, temporary_dir = _runtime(['{"content": "answer", "thinking": "private"}'])
        self.addCleanup(temporary_dir.cleanup)

        events = _pump(runtime, UserMessage("question"))

        self.assertIsInstance(events[-1], Completed)
        self.assertEqual("answer", events[-1].message.content)
        self.assertFalse(any("private" in item.content for item in llm.requests[0].messages))

    def test_invalid_reply_is_repaired_once(self) -> None:
        runtime, llm, temporary_dir = _runtime(["broken", '{"content": "repaired"}'])
        self.addCleanup(temporary_dir.cleanup)

        events = _pump(runtime, UserMessage("question"))

        self.assertIsInstance(events[-1], Completed)
        self.assertEqual(2, len(llm.requests))

    def test_invalid_reply_after_repair_fails(self) -> None:
        runtime, _, temporary_dir = _runtime(["broken", "still broken"])
        self.addCleanup(temporary_dir.cleanup)

        events = _pump(runtime, UserMessage("question"))

        self.assertEqual("invalid_model_reply", events[-1].code)

    def test_unknown_tool_returns_structured_result_to_model(self) -> None:
        runtime, _, temporary_dir = _runtime(
            ['{"content": "", "tool_call": {"name": "missing"}}', '{"content": "recovered"}'],
            definitions=(_tool("other"),),
        )
        self.addCleanup(temporary_dir.cleanup)

        events = _pump(runtime, UserMessage("question"))

        finished = next(event for event in events if isinstance(event, ToolFinished))
        self.assertIn('"code": "unknown_tool"', finished.output)
        self.assertIsInstance(events[-1], Completed)

    def test_multiple_tools_can_run_in_one_user_request(self) -> None:
        runtime, _, temporary_dir = _runtime(
            [
                '{"content": "", "tool_call": {"name": "first"}}',
                '{"content": "", "tool_call": {"name": "second"}}',
                '{"content": "done"}',
            ],
            definitions=(_tool("first"), _tool("second")),
        )
        self.addCleanup(temporary_dir.cleanup)

        events = _pump(runtime, UserMessage("question"))

        self.assertEqual(2, sum(isinstance(event, ToolFinished) for event in events))
        self.assertIsInstance(events[-1], Completed)

    def test_tool_events_expose_arguments_and_plan_projection(self) -> None:
        runtime, _, temporary_dir = _runtime(
            [
                '{"content": "", "tool_call": {"name": "create_plan", "arguments": {"items": ["查询广州", "查询杭州"]}}}',
                '{"content": "done"}',
            ],
            definitions=build_plan_tools(),
        )
        self.addCleanup(temporary_dir.cleanup)

        events = _pump(runtime, UserMessage("create a plan"))
        started = next(event for event in events if isinstance(event, ToolStarted))
        finished = next(event for event in events if isinstance(event, ToolFinished))

        self.assertEqual({"items": ["查询广州", "查询杭州"]}, started.arguments)
        self.assertIsNotNone(finished.plan)
        self.assertEqual("查询广州", finished.plan.items[0].description)

    def test_approval_and_rejection_close_the_matching_call(self) -> None:
        approved_runtime, _, approved_dir = _runtime(
            ['{"content": "", "tool_call": {"name": "delete"}}', '{"content": "done"}'],
            definitions=(_tool("delete", confirmation=ConfirmationMode.ALWAYS),),
        )
        rejected_runtime, rejected_llm, rejected_dir = _runtime(
            ['{"content": "", "tool_call": {"name": "delete"}}', '{"content": "declined"}'],
            definitions=(_tool("delete", confirmation=ConfirmationMode.ALWAYS),),
        )
        self.addCleanup(approved_dir.cleanup)
        self.addCleanup(rejected_dir.cleanup)

        approval = _pump(approved_runtime, UserMessage("question"))[-1]
        approved = _pump(approved_runtime, Approve(approval.call_id))
        rejection = _pump(rejected_runtime, UserMessage("question"))[-1]
        rejected = _pump(rejected_runtime, Reject(rejection.call_id))

        self.assertIsInstance(approval, ApprovalRequested)
        self.assertIsInstance(approved[-1], Completed)
        self.assertIsInstance(rejected[-1], Cancelled)
        self.assertEqual("Tool call delete was rejected", rejected[-1].reason)
        self.assertEqual(1, len(rejected_llm.requests))

    def test_selection_resumes_with_selected_value(self) -> None:
        runtime, _, temporary_dir = _runtime(
            ['{"content": "", "tool_call": {"name": "provide_choices", "arguments": {"question": "pick", "choices": ["a", "b"]}}}', '{"content": "selected"}'],
            definitions=build_switch_tools(),
        )
        self.addCleanup(temporary_dir.cleanup)

        requested = _pump(runtime, UserMessage("question"))[-1]
        completed = _pump(runtime, SubmitSelection(requested.request_id, "b"))

        self.assertIsInstance(requested, SelectionRequested)
        self.assertIsInstance(completed[-1], Completed)

    def test_handoff_preserves_call_id_and_waits_for_orchestrator(self) -> None:
        runtime, _, temporary_dir = _runtime(
            ['{"content": "", "tool_call": {"name": "switch_to_subagent", "arguments": {"agent_name": "resume", "context": "resume help"}}}'],
            definitions=build_switch_tools(),
        )
        self.addCleanup(temporary_dir.cleanup)

        requested = _pump(runtime, UserMessage("question"))[-1]
        handoff = runtime.handle(Approve(requested.call_id))

        self.assertIsInstance(handoff, HandoffRequested)
        self.assertEqual(requested.call_id, handoff.call_id)
        self.assertEqual(AgentKey.RESUME, handoff.target)
        self.assertEqual("run_in_progress", runtime.handle(UserMessage("new")).code)

    def test_cancel_closes_pending_tool_before_cancelled_notice(self) -> None:
        runtime, _, temporary_dir = _runtime(
            ['{"content": "", "tool_call": {"name": "delete"}}'],
            definitions=(_tool("delete", confirmation=ConfirmationMode.ALWAYS),),
        )
        self.addCleanup(temporary_dir.cleanup)

        approval = _pump(runtime, UserMessage("question"))[-1]
        closed = runtime.handle(Cancel("stop"))
        cancelled = runtime.handle(Continue())

        self.assertIsInstance(approval, ApprovalRequested)
        self.assertIsInstance(closed, ToolFinished)
        self.assertEqual(approval.call_id, closed.call_id)
        self.assertIsInstance(cancelled, Cancelled)

    def test_wrong_call_id_and_new_message_do_not_mutate_pending_state(self) -> None:
        runtime, _, temporary_dir = _runtime(
            ['{"content": "", "tool_call": {"name": "delete"}}', '{"content": "done"}'],
            definitions=(_tool("delete", confirmation=ConfirmationMode.ALWAYS),),
        )
        self.addCleanup(temporary_dir.cleanup)

        approval = _pump(runtime, UserMessage("question"))[-1]

        self.assertEqual("tool_call_mismatch", runtime.handle(Approve("wrong")).code)
        self.assertEqual("run_in_progress", runtime.handle(UserMessage("new")).code)
        self.assertIsInstance(_pump(runtime, Approve(approval.call_id))[-1], Completed)

    def test_timeout_provider_failure_and_cancel_are_typed(self) -> None:
        timeout_runtime, _, timeout_dir = _runtime([TimeoutError()])
        failure_runtime, _, failure_dir = _runtime([RuntimeError("provider down")])
        cancel_runtime, _, cancel_dir = _runtime([_cancel_during_completion])
        self.addCleanup(timeout_dir.cleanup)
        self.addCleanup(failure_dir.cleanup)
        self.addCleanup(cancel_dir.cleanup)

        self.assertEqual("timeout", _pump(timeout_runtime, UserMessage("q"))[-1].code)
        self.assertEqual("provider_failure", _pump(failure_runtime, UserMessage("q"))[-1].code)
        self.assertIsInstance(_pump(cancel_runtime, UserMessage("q"))[-1], Cancelled)

    def test_format_repair_respects_model_call_limit(self) -> None:
        runtime, _, temporary_dir = _runtime(["broken"], max_model_calls=1)
        self.addCleanup(temporary_dir.cleanup)

        events = _pump(runtime, UserMessage("question"))

        self.assertEqual("max_model_calls_exceeded", events[-1].code)

    def test_configured_timeout_is_forwarded_to_llm(self) -> None:
        runtime, llm, temporary_dir = _runtime(['{"content": "ok"}'], timeout_seconds=17)
        self.addCleanup(temporary_dir.cleanup)

        _pump(runtime, UserMessage("question"))

        self.assertEqual(17, llm.requests[0].timeout_seconds)


def _pump(runtime: AgentRuntime, command: object) -> list[object]:
    events = [runtime.handle(command)]
    while isinstance(events[-1], (Progress, ToolStarted, ToolFinished)):
        events.append(runtime.handle(Continue()))
    return events


def _runtime(
    responses: list[object],
    *,
    max_model_calls: int = 12,
    timeout_seconds: float = 60,
    definitions: tuple[ToolDefinition, ...] = (),
) -> tuple["_RuntimeDriver", "_FakeLlm", tempfile.TemporaryDirectory[str]]:
    temporary_dir = tempfile.TemporaryDirectory()
    root = Path(temporary_dir.name) / "general_agent"
    root.mkdir()
    (root / "01.md").write_text(
        "You are {{AGENT_NAME}}. <Tools>{{ADDITION_TOOLS}}</Tools> <Agents>{{SUB_AGENTS_LIST}}</Agents>",
        encoding="utf-8",
    )
    llm = _FakeLlm(responses)
    capabilities = frozenset(Capability)
    spec = AgentSpec(
        key=AgentKey.MAIN,
        display_name="main",
        description="routes",
        responsibilities=("route",),
        primary_goal="help",
        success_criteria=("answer",),
        hard_constraints=(),
        soft_constraints=(),
        style=AgentStyle("clear", "brief", "direct"),
        model_profile=ModelProfile.PRO,
        capabilities=capabilities,
    )
    catalog = ToolCatalog(definitions)
    cancellation = CancellationToken()
    plan_service = PlanService(_Ids())
    runtime = AgentRuntime(
        spec=spec,
        prompt_renderer=PromptRenderer(root.parent),
        llm=llm,
        clock=_Clock(),
        id_generator=_Ids(),
        cancellation=cancellation,
        agent_catalog=AgentCatalog((spec,)),
        tool_catalog=catalog,
        max_model_calls=max_model_calls,
        model_timeout_seconds=timeout_seconds,
        tool_executor=ToolExecutor(catalog),
        tool_context=ToolContext("session", AgentKey.MAIN, cancellation, plan=plan_service),
    )
    return _RuntimeDriver(runtime), llm, temporary_dir


class _RuntimeDriver:
    """Test-only owner of state passed to the pure runtime transition function."""

    def __init__(self, runtime: AgentRuntime) -> None:
        self._runtime = runtime
        self._state = AgentSessionState()

    def handle(self, command: object) -> object:
        transition = self._runtime.advance(self._state, command)
        self._state = transition.state
        return transition.event


class _FakeLlm:
    def __init__(self, responses: list[object]) -> None:
        self._responses = list(responses)
        self.requests: list[LLMRequest] = []

    def complete(self, request: LLMRequest, cancellation: CancellationSignal) -> LLMResult:
        self.requests.append(request)
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        if callable(response):
            response = response(cancellation)
        return LLMResult(content=response)

    def close(self) -> None:
        pass


def _cancel_during_completion(cancellation: CancellationSignal) -> str:
    cancellation.cancel()
    return '{"content": "discarded"}'


class _Clock:
    def now(self) -> datetime:
        return datetime(2026, 1, 1, tzinfo=timezone.utc)


class _Ids:
    def __init__(self) -> None:
        self._number = 0

    def new_id(self) -> str:
        self._number += 1
        return f"id-{self._number}"


def _tool(
    name: str,
    *,
    confirmation: ConfirmationMode = ConfirmationMode.NEVER,
) -> ToolDefinition:
    return ToolDefinition(
        name=name,
        description=name,
        schema=ToolSchema(properties={}),
        policy=ToolPolicy(confirmation=confirmation),
        handler=lambda arguments, context: ToolSuccess({"tool": name}),
    )
