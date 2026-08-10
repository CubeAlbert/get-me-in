"""Tests for the pull-driven typed agent runtime."""

from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from src.get_me_in.application.agent_catalog import AgentCatalog
from src.get_me_in.application.cancellation import CancellationToken
from src.get_me_in.application.commands import Approve, Cancel, CancelSelection, Continue, FailHandoff, Reject, SubmitSelection, UserMessage
from src.get_me_in.application.events import (
    ApprovalRequested,
    Cancelled,
    Completed,
    Failed,
    HandoffRequested,
    Paused,
    Progress,
    ProgressKind,
    SelectionRequested,
    ToolFinished,
    ToolStarted,
)
from src.get_me_in.application.localization import Locale
from src.get_me_in.application.prompt_renderer import PromptRenderer
from src.get_me_in.application.plan_service import PlanService
from src.get_me_in.application.runtime import AgentRuntime
from src.get_me_in.application.tool_catalog import ToolCatalog
from src.get_me_in.application.tool_executor import ToolContext, ToolExecutor
from src.get_me_in.domain.agents import AgentKey, AgentSpec, AgentStyle, Capability
from src.get_me_in.domain.llm_usage import (
    LLMAttemptOutcome,
    ReportedUsage,
    TokenUsage,
)
from src.get_me_in.domain.sessions import AgentSessionState
from src.get_me_in.domain.tools import ConfirmationMode, ToolDefinition, ToolPolicy, ToolSchema, ToolSuccess
from src.get_me_in.ports.llm import CancellationSignal, LLMRequest, LLMResult, ModelProfile
from src.get_me_in.tools.switch import build_switch_tools
from src.get_me_in.tools.plan import build_plan_tools


class RuntimeTests(unittest.TestCase):
    def test_provider_response_records_completed_attempt_and_metadata(self) -> None:
        result = LLMResult(
            content=_finish("answer", "private"),
            response_model="actual-provider-model",
            usage=ReportedUsage(TokenUsage(12, 4, cached_input_tokens=2)),
        )
        runtime, _, temporary_dir = _runtime([result])
        self.addCleanup(temporary_dir.cleanup)

        _pump(runtime, UserMessage("question"))

        attempt = runtime.last_transition.attempt
        self.assertIsNotNone(attempt)
        self.assertEqual(LLMAttemptOutcome.COMPLETED, attempt.outcome)
        self.assertEqual("actual-provider-model", attempt.response_model)
        self.assertEqual(12, attempt.usage.value.input_tokens)

    def test_user_message_completes_and_never_replays_thinking(self) -> None:
        runtime, llm, temporary_dir = _runtime([_finish("answer", "private")])
        self.addCleanup(temporary_dir.cleanup)

        events = _pump(runtime, UserMessage("question"))

        self.assertEqual(ProgressKind.CALLING_MODEL, events[0].kind)
        self.assertIsInstance(events[-1], Completed)
        self.assertEqual("answer", events[-1].message.content)
        self.assertEqual("private", events[-1].message.thinking)
        self.assertFalse(any("private" in item.content for item in llm.requests[0].messages))

    def test_plain_text_reply_uses_one_model_repair_after_local_repair_fails(self) -> None:
        runtime, llm, temporary_dir = _runtime(
            ["plain **markdown** answer", _finish("repaired", "summary")]
        )
        self.addCleanup(temporary_dir.cleanup)

        events = _pump(runtime, UserMessage("question"))

        self.assertIsInstance(events[-1], Completed)
        self.assertEqual(2, len(llm.requests))
        self.assertEqual("repaired", events[-1].message.content)
        repair_message = llm.requests[1].messages[-1]
        self.assertEqual("system", repair_message.role.value)
        self.assertIn("Model response must be a JSON object", repair_message.content)
        self.assertIn("<OutputFormat>canonical contract</OutputFormat>", repair_message.content)

    def test_malformed_json_is_repaired_locally_without_another_model_call(self) -> None:
        runtime, llm, temporary_dir = _runtime(
            ['{"event_type":"finish","message":"answer","thinking":"summary",}']
        )
        self.addCleanup(temporary_dir.cleanup)

        events = _pump(runtime, UserMessage("question"))

        self.assertIsInstance(events[-1], Completed)
        self.assertEqual(1, len(llm.requests))
        self.assertEqual("answer", events[-1].message.content)

    def test_extra_model_fields_are_ignored_without_format_repair(self) -> None:
        runtime, llm, temporary_dir = _runtime(
            [
                json.dumps(
                    {
                        "id": "untrusted",
                        "role": "user",
                        "timestamp": "wrong",
                        "tool_call_id": "untrusted-call",
                        "plan_status": {"current": "wrong"},
                        "unknown": "ignored",
                        "event_type": "finish",
                        "message": "answer",
                        "thinking": "summary",
                    }
                )
            ]
        )
        self.addCleanup(temporary_dir.cleanup)

        events = _pump(runtime, UserMessage("question"))

        self.assertIsInstance(events[-1], Completed)
        self.assertEqual(1, len(llm.requests))
        self.assertNotEqual("untrusted", events[-1].message.event_id)
        self.assertEqual("answer", events[-1].message.content)

    def test_empty_finish_thinking_is_accepted_without_repair(self) -> None:
        runtime, llm, temporary_dir = _runtime(
            [_finish("answer", "")]
        )
        self.addCleanup(temporary_dir.cleanup)

        events = _pump(runtime, UserMessage("question"))

        self.assertIsInstance(events[-1], Completed)
        self.assertEqual(1, len(llm.requests))
        self.assertEqual("answer", events[-1].message.content)
        self.assertEqual("", events[-1].message.thinking)

    def test_unrecoverable_reply_pauses_after_three_model_repairs(self) -> None:
        runtime, llm, temporary_dir = _runtime(
            [
                '["ambiguous", "structure"]',
                '["still", "ambiguous"]',
                '["third", "ambiguous"]',
                '["fourth", "ambiguous"]',
            ]
        )
        self.addCleanup(temporary_dir.cleanup)

        events = _pump(runtime, UserMessage("question"))

        self.assertIsInstance(events[-1], Paused)
        self.assertEqual("invalid_model_reply", events[-1].code)
        self.assertEqual(4, len(llm.requests))

    def test_format_repair_limit_zero_pauses_without_repair(self) -> None:
        runtime, llm, temporary_dir = _runtime(
            ["bad response"], format_repair_limit=0
        )
        self.addCleanup(temporary_dir.cleanup)

        events = _pump(runtime, UserMessage("question"))

        self.assertIsInstance(events[-1], Paused)
        self.assertEqual(1, len(llm.requests))
        self.assertIn("0 repair attempts", events[-1].message)

    def test_format_repair_limit_one_pauses_after_one_repair(self) -> None:
        runtime, llm, temporary_dir = _runtime(
            ["bad response 1", "bad response 2"], format_repair_limit=1
        )
        self.addCleanup(temporary_dir.cleanup)

        events = _pump(runtime, UserMessage("question"))

        self.assertIsInstance(events[-1], Paused)
        self.assertEqual(2, len(llm.requests))
        self.assertIn("1 repair attempts", events[-1].message)

    def test_new_user_message_clears_format_repair_budget(self) -> None:
        runtime, llm, temporary_dir = _runtime(
            [
                "bad response 1",
                "bad response 2",
                "bad response 3",
                "bad response 4",
                _finish("recovered on a new turn", ""),
            ]
        )
        self.addCleanup(temporary_dir.cleanup)

        paused = _pump(runtime, UserMessage("first question"))[-1]
        completed = _pump(runtime, UserMessage("second question"))[-1]

        self.assertIsInstance(paused, Paused)
        self.assertIsInstance(completed, Completed)
        self.assertEqual(5, len(llm.requests))

    def test_repair_budget_survives_a_tool_call_within_the_same_turn(self) -> None:
        runtime, llm, temporary_dir = _runtime(
            [
                _tool_call("inspect"),
                "bad response after tool",
                "another bad response after tool",
                _finish("recovered", ""),
            ],
            definitions=(_tool("inspect"),),
        )
        self.addCleanup(temporary_dir.cleanup)

        events = _pump(runtime, UserMessage("inspect then answer"))

        self.assertIsInstance(events[-1], Completed)
        self.assertEqual(4, len(llm.requests))

    def test_semantic_error_uses_model_repair_without_local_default(self) -> None:
        runtime, llm, temporary_dir = _runtime(
            [
                '{"event_type":"finish","message":"invalid thinking","thinking":1}',
                _finish("repaired", "summary"),
            ]
        )
        self.addCleanup(temporary_dir.cleanup)

        events = _pump(runtime, UserMessage("question"))

        self.assertIsInstance(events[-1], Completed)
        self.assertEqual(2, len(llm.requests))
        self.assertEqual("repaired", events[-1].message.content)

    def test_empty_tool_message_repairs_before_executing_the_tool(self) -> None:
        executions: list[str] = []
        runtime, llm, temporary_dir = _runtime(
            [
                _tool_call("inspect", message=""),
                _tool_call("inspect", message="**Inspecting**"),
                _finish("done", "summary"),
            ],
            definitions=(
                _tool(
                    "inspect",
                    handler=lambda arguments, context: executions.append("inspect") or ToolSuccess("ok"),
                ),
            ),
        )
        self.addCleanup(temporary_dir.cleanup)

        events = _pump(runtime, UserMessage("inspect"))

        self.assertEqual(["inspect"], executions)
        self.assertEqual(1, sum(isinstance(event, ToolStarted) for event in events))
        self.assertEqual(3, len(llm.requests))
        self.assertIsInstance(events[-1], Completed)

    def test_unknown_tool_returns_structured_result_to_model(self) -> None:
        runtime, _, temporary_dir = _runtime(
            [_tool_call("missing"), _finish("recovered", "fixed")],
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
                _tool_call("first"),
                _tool_call("second"),
                _finish("done", "done"),
            ],
            definitions=(_tool("first"), _tool("second")),
        )
        self.addCleanup(temporary_dir.cleanup)

        events = _pump(runtime, UserMessage("question"))

        self.assertEqual(2, sum(isinstance(event, ToolFinished) for event in events))
        self.assertIsInstance(events[-1], Completed)

    def test_tool_events_expose_arguments_and_plan_projection(self) -> None:
        runtime, llm, temporary_dir = _runtime(
            [
                _tool_call(
                    "create_plan",
                    {"items": ["查询广州", "查询杭州"]},
                    thinking="planning",
                ),
                _finish("done", "done"),
            ],
            definitions=build_plan_tools(),
        )
        self.addCleanup(temporary_dir.cleanup)

        events = _pump(runtime, UserMessage("create a plan"))
        started = next(event for event in events if isinstance(event, ToolStarted))
        finished = next(event for event in events if isinstance(event, ToolFinished))

        self.assertEqual({"items": ["查询广州", "查询杭州"]}, started.arguments)
        self.assertEqual("Calling tool create_plan", started.message)
        self.assertEqual("planning", started.thinking)
        self.assertIsNotNone(finished.plan)
        self.assertEqual("查询广州", finished.plan.items[0].description)
        tool_result = json.loads(llm.requests[1].messages[-1].content)
        self.assertEqual(
            {
                "current": "0|查询广州",
                "completed": [],
                "remaining": ["1|查询杭州"],
            },
            tool_result["plan_status"],
        )

    def test_plan_projection_uses_snapshot_change_not_tool_name(self) -> None:
        def create_custom_plan(arguments: object, context: object) -> ToolSuccess:
            del arguments
            assert context.plan is not None
            context.plan.create(("custom step",))
            return ToolSuccess({"created": True})

        runtime, _, temporary_dir = _runtime(
            [
                _tool_call("custom_plan_mutation"),
                _tool_call("inspect"),
                _finish("done", "done"),
            ],
            definitions=(
                _tool("custom_plan_mutation", handler=create_custom_plan),
                _tool("inspect"),
            ),
        )
        self.addCleanup(temporary_dir.cleanup)

        events = _pump(runtime, UserMessage("create and inspect"))

        finished = [event for event in events if isinstance(event, ToolFinished)]
        self.assertEqual(2, len(finished))
        self.assertIsNotNone(finished[0].plan)
        self.assertEqual("custom step", finished[0].plan.items[0].description)
        self.assertIsNone(finished[1].plan)

    def test_approval_and_rejection_close_the_matching_call(self) -> None:
        approved_runtime, _, approved_dir = _runtime(
            [_tool_call("delete"), _finish("done", "done")],
            definitions=(_tool("delete", confirmation=ConfirmationMode.ALWAYS),),
        )
        rejected_runtime, rejected_llm, rejected_dir = _runtime(
            [_tool_call("delete"), _finish("declined", "declined")],
            definitions=(_tool("delete", confirmation=ConfirmationMode.ALWAYS),),
        )
        self.addCleanup(approved_dir.cleanup)
        self.addCleanup(rejected_dir.cleanup)

        approval = _pump(approved_runtime, UserMessage("question"))[-1]
        approved = _pump(approved_runtime, Approve(approval.call_id))
        rejection = _pump(rejected_runtime, UserMessage("question"))[-1]
        rejected = _pump(rejected_runtime, Reject(rejection.call_id))

        self.assertIsInstance(approval, ApprovalRequested)
        self.assertEqual("delete", approval.tool_name)
        self.assertIsInstance(approved[-1], Completed)
        self.assertIsInstance(rejected[-1], Paused)
        self.assertEqual("approval_rejected", rejected[-1].code)
        self.assertEqual("Tool call delete was rejected", rejected[-1].message)
        continued = _pump(rejected_runtime, UserMessage("continue after rejection"))
        self.assertIsInstance(continued[-1], Completed)
        self.assertEqual(2, len(rejected_llm.requests))
        previous = json.loads(rejected_llm.requests[1].messages[-2].content)
        current = json.loads(rejected_llm.requests[1].messages[-1].content)
        self.assertEqual("tool_call_result", previous["event_type"])
        self.assertEqual("rejected", previous["event_payload"]["code"])
        self.assertEqual("user_input", current["event_type"])
        self.assertEqual("continue after rejection", current["message"])

    def test_selection_resumes_with_selected_value(self) -> None:
        runtime, _, temporary_dir = _runtime(
            [
                _tool_call(
                    "provide_choices",
                    {"question": "pick", "choices": ["a", "b"]},
                ),
                _finish("selected", "selected"),
            ],
            definitions=build_switch_tools(),
        )
        self.addCleanup(temporary_dir.cleanup)

        requested = _pump(runtime, UserMessage("question"))[-1]
        completed = _pump(runtime, SubmitSelection(requested.request_id, "b"))

        self.assertIsInstance(requested, SelectionRequested)
        self.assertIsInstance(completed[-1], Completed)

    def test_tool_call_metadata_mixed_into_arguments_is_ignored(self) -> None:
        runtime, _, temporary_dir = _runtime(
            [
                _tool_call(
                    "provide_choices",
                    {
                        "question": "pick",
                        "choices": ["a", "b"],
                        "thinking": "model summary",
                    },
                )
            ],
            definitions=build_switch_tools(),
        )
        self.addCleanup(temporary_dir.cleanup)

        requested = _pump(runtime, UserMessage("question"))[-1]

        self.assertIsInstance(requested, SelectionRequested)
        self.assertEqual("pick", requested.prompt)
        self.assertEqual(("a", "b"), requested.choices)

    def test_selection_cancellation_pauses_until_next_user_message(self) -> None:
        runtime, llm, temporary_dir = _runtime(
            [
                _tool_call(
                    "provide_choices",
                    {"question": "pick", "choices": ["a", "b"]},
                ),
                _finish("still active", "continued"),
            ],
            definitions=build_switch_tools(),
        )
        self.addCleanup(temporary_dir.cleanup)

        requested = _pump(runtime, UserMessage("question"))[-1]
        cancelled = runtime.handle(CancelSelection(requested.request_id))

        self.assertIsInstance(requested, SelectionRequested)
        self.assertIsInstance(cancelled, Paused)
        self.assertEqual("selection_cancelled", cancelled.code)
        self.assertEqual(1, len(llm.requests))

        completed = _pump(runtime, UserMessage("continue after cancelling the choices"))

        self.assertIsInstance(completed[-1], Completed)
        self.assertEqual(2, len(llm.requests))
        tool_result = json.loads(llm.requests[1].messages[-2].content)
        self.assertEqual(
            {
                "code": "cancelled",
                "message": "Selection cancelled by user",
            },
            tool_result["event_payload"],
        )
        self.assertIn("continue after cancelling the choices", llm.requests[1].messages[-1].content)

    def test_handoff_preserves_call_id_and_waits_for_orchestrator(self) -> None:
        runtime, _, temporary_dir = _runtime(
            [
                _tool_call(
                    "switch_to_subagent",
                    {"agent_name": "resume", "context": "resume help"},
                )
            ],
            definitions=build_switch_tools(),
        )
        self.addCleanup(temporary_dir.cleanup)

        requested = _pump(runtime, UserMessage("question"))[-1]
        handoff = runtime.handle(Approve(requested.call_id))

        self.assertIsInstance(handoff, HandoffRequested)
        self.assertEqual(requested.call_id, handoff.call_id)
        self.assertEqual(AgentKey.RESUME, handoff.target)
        self.assertEqual("run_in_progress", runtime.handle(UserMessage("new")).code)

    def test_terminal_handoff_failure_allows_the_next_user_message(self) -> None:
        runtime, _, temporary_dir = _runtime(
            [
                _tool_call(
                    "switch_to_subagent",
                    {"agent_name": "resume", "context": "resume help"},
                )
            ],
            definitions=build_switch_tools(),
        )
        self.addCleanup(temporary_dir.cleanup)

        approval = _pump(runtime, UserMessage("question"))[-1]
        requested = runtime.handle(Approve(approval.call_id))
        failed = runtime.handle(
            FailHandoff(
                requested.call_id,
                "subagent_failed",
                "Model response remained invalid after three repair attempts",
                terminal=True,
            )
        )

        self.assertIsInstance(failed, Failed)
        self.assertEqual("subagent_failed", failed.code)
        self.assertIsInstance(runtime.handle(UserMessage("new question")), Progress)

    def test_invalid_model_reply_logs_the_complete_raw_message(self) -> None:
        first_raw = "first invalid response " + ("A" * 700)
        second_raw = "second invalid response " + ("B" * 700)
        third_raw = "third invalid response " + ("C" * 700)
        fourth_raw = "fourth invalid response " + ("D" * 700)
        runtime, _, temporary_dir = _runtime([first_raw, second_raw, third_raw, fourth_raw])
        self.addCleanup(temporary_dir.cleanup)

        with self.assertLogs("src.get_me_in.application.runtime", level="WARNING") as captured:
            events = _pump(runtime, UserMessage("question"))

        self.assertEqual("invalid_model_reply", events[-1].code)
        log_text = "\n".join(captured.output)
        self.assertIn(repr(first_raw), log_text)
        self.assertIn(repr(second_raw), log_text)

    def test_cancel_closes_pending_tool_before_cancelled_notice(self) -> None:
        runtime, _, temporary_dir = _runtime(
            [_tool_call("delete")],
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
            [_tool_call("delete"), _finish("done", "done")],
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

    def test_model_repair_respects_model_call_limit(self) -> None:
        runtime, _, temporary_dir = _runtime(["plain text"], max_model_calls=1)
        self.addCleanup(temporary_dir.cleanup)

        events = _pump(runtime, UserMessage("question"))

        self.assertEqual("max_model_calls_exceeded", events[-1].code)

    def test_configured_timeout_is_forwarded_to_llm(self) -> None:
        runtime, llm, temporary_dir = _runtime([_finish("ok", "ok")], timeout_seconds=17)
        self.addCleanup(temporary_dir.cleanup)

        _pump(runtime, UserMessage("question"))

        self.assertEqual(17, llm.requests[0].timeout_seconds)

    def test_agent_spec_temperature_is_forwarded_to_llm(self) -> None:
        runtime, llm, temporary_dir = _runtime([_finish("ok", "ok")])
        self.addCleanup(temporary_dir.cleanup)

        _pump(runtime, UserMessage("question"))

        self.assertEqual(0.1, llm.requests[0].temperature)

    def test_tool_context_uses_session_id_of_current_transition(self) -> None:
        observed_session_ids: list[str] = []
        runtime, _, temporary_dir = _runtime(
            [
                _tool_call("inspect"),
                _finish("done", "done"),
            ],
            definitions=(_tool("inspect", handler=lambda arguments, context: observed_session_ids.append(context.session_id) or ToolSuccess("ok")),),
        )
        self.addCleanup(temporary_dir.cleanup)

        runtime.handle(UserMessage("question"))
        started = runtime.handle(Continue())
        runtime.session_id = "restored-session"
        _pump(runtime, Continue())

        self.assertIsInstance(started, ToolStarted)
        self.assertEqual(["restored-session"], observed_session_ids)


def _pump(runtime: AgentRuntime, command: object) -> list[object]:
    events = [runtime.handle(command)]
    while isinstance(events[-1], (Progress, ToolStarted, ToolFinished)):
        events.append(runtime.handle(Continue()))
    return events


def _runtime(
    responses: list[object],
    *,
    max_model_calls: int = 100,
    timeout_seconds: float = 60,
    format_repair_limit: int = 3,
    definitions: tuple[ToolDefinition, ...] = (),
) -> tuple["_RuntimeDriver", "_FakeLlm", tempfile.TemporaryDirectory[str]]:
    temporary_dir = tempfile.TemporaryDirectory()
    root = Path(temporary_dir.name) / "general_agent"
    root.mkdir()
    (root / "01.md").write_text(
        "You are {{AGENT_NAME}}. <Tools>{{ADDITION_TOOLS}}</Tools> <Agents>{{SUB_AGENTS_LIST}}</Agents>",
        encoding="utf-8",
    )
    (root / "09_output_format.md").write_text(
        "<OutputFormat>canonical contract</OutputFormat>", encoding="utf-8"
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
        temperature=0.1,
        capabilities=capabilities,
    )
    catalog = ToolCatalog(definitions)
    cancellation = CancellationToken()
    plan_service = PlanService(_Ids())
    runtime = AgentRuntime(
        spec=spec,
        prompt_renderer=PromptRenderer(
            root.parent,
            response_locale=Locale.ZH_CN,
        ),
        llm=llm,
        clock=_Clock(),
        id_generator=_Ids(),
        cancellation=cancellation,
        agent_catalog=AgentCatalog((spec,)),
        tool_catalog=catalog,
        max_model_calls=max_model_calls,
        model_timeout_seconds=timeout_seconds,
        format_repair_limit=format_repair_limit,
        tool_executor=ToolExecutor(catalog),
        tool_context=ToolContext("session", AgentKey.MAIN, cancellation, plan=plan_service),
    )
    return _RuntimeDriver(runtime), llm, temporary_dir


class _RuntimeDriver:
    """Test-only owner of state passed to the pure runtime transition function."""

    def __init__(self, runtime: AgentRuntime) -> None:
        self._runtime = runtime
        self._state = AgentSessionState()
        self.session_id = "session"
        self.last_transition = None

    def handle(self, command: object) -> object:
        transition = self._runtime.advance(self._state, command, session_id=self.session_id)
        self._state = transition.state
        self.last_transition = transition
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
        if isinstance(response, LLMResult):
            return response
        return LLMResult(content=response)

    def close(self) -> None:
        pass


def _cancel_during_completion(cancellation: CancellationSignal) -> str:
    cancellation.cancel()
    return _finish("discarded", "discarded")


def _finish(message: str, thinking: str) -> str:
    return json.dumps(
        {
            "event_type": "finish",
            "message": message,
            "thinking": thinking,
        },
        ensure_ascii=False,
    )


def _tool_call(
    name: str,
    arguments: dict[str, object] | None = None,
    *,
    thinking: str | None = None,
    message: str | None = None,
) -> str:
    payload: dict[str, object] = {
        "event_type": "tool_call",
        "message": message if message is not None else f"Calling tool {name}",
        "tool": name,
        "event_payload": arguments or {},
    }
    if thinking is not None:
        payload["thinking"] = thinking
    return json.dumps(payload, ensure_ascii=False)


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
    handler=None,
) -> ToolDefinition:
    return ToolDefinition(
        name=name,
        purpose=name,
        use_when="when needed",
        do_not_use_when="otherwise",
        expected_output="typed output",
        schema=ToolSchema(properties={}),
        policy=ToolPolicy(confirmation=confirmation),
        handler=handler or (lambda arguments, context: ToolSuccess({"tool": name})),
    )
