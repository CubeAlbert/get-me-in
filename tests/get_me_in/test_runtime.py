"""Tests for R2's synchronous typed agent runtime."""

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from src.get_me_in.application.cancellation import CancellationToken
from src.get_me_in.application.commands import Cancel, UserMessage
from src.get_me_in.application.events import Cancelled, Completed, Failed, ToolFinished, ToolStarted
from src.get_me_in.application.prompt_renderer import PromptRenderer
from src.get_me_in.application.runtime import AgentRuntime
from src.get_me_in.domain.agents import AgentKey, AgentSpec, AgentStyle, Capability
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

    def test_unknown_tool_emits_typed_tool_and_failure_events(self) -> None:
        runtime, _, temporary_dir = _runtime(['{"content": "", "tool_call": {"name": "missing"}}'])
        self.addCleanup(temporary_dir.cleanup)

        events = runtime.handle(UserMessage("question"))

        self.assertTrue(any(isinstance(event, ToolStarted) for event in events))
        self.assertTrue(any(isinstance(event, ToolFinished) for event in events))
        self.assertEqual("unknown_tool", events[-1].code)

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


def _runtime(
    responses: list[object],
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
        return LLMResult(content=response)


class _Clock:
    def now(self) -> datetime:
        return datetime(2026, 1, 1, tzinfo=timezone.utc)


class _Ids:
    def __init__(self) -> None:
        self._number = 0

    def new_id(self) -> str:
        self._number += 1
        return f"id-{self._number}"
