"""Tests for R2's synchronous typed agent runtime."""

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from src.get_me_in.application.cancellation import CancellationToken
from src.get_me_in.application.commands import Approve, Cancel, Reject, SubmitSelection, ToolResult, UserMessage
from src.get_me_in.application.events import ApprovalRequested, Cancelled, Completed, Failed, Handoff, SelectionRequested, ToolFinished, ToolStarted
from src.get_me_in.application.prompt_renderer import PromptRenderer
from src.get_me_in.application.runtime import AgentRuntime
from src.get_me_in.application.tool_catalog import ToolCatalog
from src.get_me_in.application.tool_executor import ToolContext, ToolExecutor
from src.get_me_in.domain.agents import AgentKey, AgentSpec, AgentStyle, Capability
from src.get_me_in.domain.tools import ConfirmationMode, ToolDefinition, ToolPolicy, ToolSchema, ToolSuccess
from src.get_me_in.tools.switch import build_switch_tools
from src.get_me_in.ports.llm import CancellationSignal, LLMRequest, LLMResult, ModelProfile


class RuntimeTests(unittest.TestCase):
    def test_user_message_completes_and_never_replays_thinking(self) -> None:
        runtime, llm, temporary_dir = _runtime(['{"content": "answer", "thinking": "private"}'])
        self.addCleanup(temporary_dir.cleanup)

        events = runtime.handle(UserMessage("question"))

        self.assertIsInstance(events[-1], Completed)
        self.assertEqual("answer", events[-1].message.content)
        self.assertFalse(any("private" in item.content for item in llm.requests[0].messages))

    def test_invalid_reply_is_repaired_once(self) -> None:
        runtime, llm, temporary_dir = _runtime(["broken", '{"content": "repaired"}'])
        self.addCleanup(temporary_dir.cleanup)

        events = runtime.handle(UserMessage("question"))

        self.assertIsInstance(events[-1], Completed)
        self.assertEqual(2, len(llm.requests))

    def test_invalid_reply_after_repair_fails(self) -> None:
        runtime, _, temporary_dir = _runtime(["broken", "still broken"])
        self.addCleanup(temporary_dir.cleanup)

        events = runtime.handle(UserMessage("question"))

        self.assertEqual("invalid_model_reply", events[-1].code)

    def test_unknown_catalog_tool_returns_structured_result_to_model(self) -> None:
        runtime, _, temporary_dir = _runtime(
            [
                '{"content": "", "tool_call": {"name": "missing"}}',
                '{"content": "recovered"}',
            ],
            tool_executor=_executor(_tool("other")),
        )
        self.addCleanup(temporary_dir.cleanup)

        events = runtime.handle(UserMessage("question"))

        self.assertTrue(any(isinstance(event, ToolStarted) for event in events))
        self.assertTrue(any(isinstance(event, ToolFinished) for event in events))
        finished = next(event for event in events if isinstance(event, ToolFinished))
        self.assertIn('"code": "unknown_tool"', finished.output)
        self.assertIsInstance(events[-1], Completed)

    def test_catalog_tool_executes_and_resumes_model(self) -> None:
        runtime, _, temporary_dir = _runtime(
            [
                '{"content": "", "tool_call": {"name": "search"}}',
                '{"content": "final answer"}',
            ],
            tool_executor=_executor(_tool("search")),
        )
        self.addCleanup(temporary_dir.cleanup)

        events = runtime.handle(UserMessage("question"))

        self.assertTrue(any(isinstance(event, ToolStarted) for event in events))
        self.assertTrue(any(isinstance(event, ToolFinished) for event in events))
        self.assertIsInstance(events[-1], Completed)

    def test_approval_round_trip_executes_after_explicit_approval(self) -> None:
        runtime, _, temporary_dir = _runtime(
            [
                '{"content": "", "tool_call": {"name": "delete"}}',
                '{"content": "final answer"}',
            ],
            tool_executor=_executor(_tool("delete", confirmation=ConfirmationMode.ALWAYS)),
        )
        self.addCleanup(temporary_dir.cleanup)

        requested = runtime.handle(UserMessage("question"))
        approved = runtime.handle(Approve(requested[-1].call_id))

        self.assertIsInstance(requested[-1], ApprovalRequested)
        self.assertTrue(any(isinstance(event, ToolFinished) for event in approved))
        self.assertIsInstance(approved[-1], Completed)

    def test_rejection_returns_tool_failure_to_the_model(self) -> None:
        runtime, _, temporary_dir = _runtime(
            [
                '{"content": "", "tool_call": {"name": "delete"}}',
                '{"content": "declined"}',
            ],
            tool_executor=_executor(_tool("delete", confirmation=ConfirmationMode.ALWAYS)),
        )
        self.addCleanup(temporary_dir.cleanup)

        requested = runtime.handle(UserMessage("question"))
        rejected = runtime.handle(Reject(requested[-1].call_id))

        self.assertIsInstance(rejected[0], ToolFinished)
        self.assertIn('"code": "rejected"', rejected[0].output)
        self.assertIsInstance(rejected[-1], Completed)

    def test_catalog_filters_tools_by_agent_capability(self) -> None:
        runtime, _, temporary_dir = _runtime(
            [
                '{"content": "", "tool_call": {"name": "resume_read"}}',
                '{"content": "not available"}',
            ],
            tool_executor=_executor(
                _tool("resume_read", capabilities=frozenset({Capability.RESUME_WORKSPACE}))
            ),
        )
        self.addCleanup(temporary_dir.cleanup)

        events = runtime.handle(UserMessage("question"))

        finished = next(event for event in events if isinstance(event, ToolFinished))
        self.assertIn('"code": "tool_not_permitted"', finished.output)
        self.assertIsInstance(events[-1], Completed)

    def test_selection_interaction_resumes_with_selected_value(self) -> None:
        runtime, _, temporary_dir = _runtime(
            ['{"content": "", "tool_call": {"name": "provide_choices", "arguments": {"question": "pick", "choices": ["a", "b"]}}}', '{"content": "selected"}'],
            tool_executor=ToolExecutor(ToolCatalog(build_switch_tools())),
        )
        self.addCleanup(temporary_dir.cleanup)
        requested = runtime.handle(UserMessage("question"))
        completed = runtime.handle(SubmitSelection(requested[-1].request_id, "b"))
        self.assertIsInstance(requested[-1], SelectionRequested)
        self.assertIsInstance(completed[-1], Completed)

    def test_subagent_switch_emits_typed_handoff(self) -> None:
        runtime, _, temporary_dir = _runtime(
            ['{"content": "", "tool_call": {"name": "switch_to_subagent", "arguments": {"agent_name": "resume", "context": "resume help"}}}'],
            tool_executor=ToolExecutor(ToolCatalog(build_switch_tools())),
        )
        self.addCleanup(temporary_dir.cleanup)
        requested = runtime.handle(UserMessage("question"))
        events = runtime.handle(Approve(requested[-1].call_id))
        self.assertIsInstance(events[-1], Handoff)
        self.assertEqual(AgentKey.RESUME, events[-1].target)

    def test_approval_rejects_the_wrong_call_id(self) -> None:
        runtime, _, temporary_dir = _runtime(
            ['{"content": "", "tool_call": {"name": "search"}}'],
            tool_executor=_executor(_tool("search", confirmation=ConfirmationMode.ALWAYS)),
        )
        self.addCleanup(temporary_dir.cleanup)
        runtime.handle(UserMessage("question"))

        events = runtime.handle(Approve(call_id="wrong"))

        self.assertEqual("tool_call_mismatch", events[-1].code)

    def test_timeout_and_provider_failures_are_typed(self) -> None:
        timeout_runtime, _, timeout_dir = _runtime([TimeoutError()])
        failure_runtime, _, failure_dir = _runtime([RuntimeError("provider down")])
        self.addCleanup(timeout_dir.cleanup)
        self.addCleanup(failure_dir.cleanup)

        self.assertEqual("timeout", timeout_runtime.handle(UserMessage("q"))[-1].code)
        self.assertEqual("provider_failure", failure_runtime.handle(UserMessage("q"))[-1].code)

    def test_cancel_resets_for_the_next_user_message(self) -> None:
        runtime, _, temporary_dir = _runtime(['{"content": "after cancel"}'])
        self.addCleanup(temporary_dir.cleanup)

        cancelled = runtime.handle(Cancel())
        completed = runtime.handle(UserMessage("question"))

        self.assertIsInstance(cancelled[-1], Cancelled)
        self.assertIsInstance(completed[-1], Completed)

    def test_cancellation_during_completion_allows_the_next_request(self) -> None:
        runtime, _, temporary_dir = _runtime(
            [_cancel_during_completion, '{"content": "after cancellation"}']
        )
        self.addCleanup(temporary_dir.cleanup)

        cancelled = runtime.handle(UserMessage("first"))
        completed = runtime.handle(UserMessage("second"))

        self.assertIsInstance(cancelled[-1], Cancelled)
        self.assertIsInstance(completed[-1], Completed)

    def test_format_repair_respects_max_rounds(self) -> None:
        runtime, _, temporary_dir = _runtime(["broken"], max_rounds=1)
        self.addCleanup(temporary_dir.cleanup)

        events = runtime.handle(UserMessage("question"))

        self.assertEqual("max_rounds_exceeded", events[-1].code)


def _runtime(
    responses: list[object],
    *,
    max_rounds: int = 2,
    tool_executor: ToolExecutor | None = None,
) -> tuple[AgentRuntime, "_FakeLlm", tempfile.TemporaryDirectory[str]]:
    temporary_dir = tempfile.TemporaryDirectory()
    root = Path(temporary_dir.name) / "general_agent"
    root.mkdir()
    (root / "01.md").write_text("You are {{AGENT_NAME}}.", encoding="utf-8")
    llm = _FakeLlm(responses)
    runtime = AgentRuntime(
        spec=AgentSpec(
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
            capabilities=frozenset({Capability.ROUTE}),
        ),
        prompt_renderer=PromptRenderer(root.parent),
        llm=llm,
        clock=_Clock(),
        id_generator=_Ids(),
        cancellation=CancellationToken(),
        max_rounds=max_rounds,
        tool_executor=tool_executor,
        tool_context=ToolContext("session", AgentKey.MAIN, CancellationToken()),
    )
    return runtime, llm, temporary_dir


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
            response(cancellation)
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


def _executor(definition: ToolDefinition) -> ToolExecutor:
    return ToolExecutor(ToolCatalog((definition,)))


def _tool(
    name: str,
    *,
    confirmation: ConfirmationMode = ConfirmationMode.NEVER,
    capabilities: frozenset[Capability] = frozenset(),
) -> ToolDefinition:
    return ToolDefinition(
        name=name,
        description=name,
        schema=ToolSchema(properties={}),
        policy=ToolPolicy(required_capabilities=capabilities, confirmation=confirmation),
        handler=lambda arguments, context: ToolSuccess({"tool": name}),
    )
