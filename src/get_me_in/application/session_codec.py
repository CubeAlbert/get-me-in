"""Disk-safe codec for session snapshots, separate from model conversation codec."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation

from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.llm_usage import (
    CostEstimateBasis,
    CostUnavailable,
    CostUnavailableReason,
    EstimatedCost,
    LLMAttemptOutcome,
    LLMAttemptPurpose,
    LLMAttemptReason,
    LLMAttemptRecord,
    LLMAttemptScope,
    ModelProfile,
    ReportedUsage,
    TokenUsage,
    UnavailableUsage,
    UsageUnavailableReason,
)
from src.get_me_in.domain.messages import MessageRecord, Role, ToolCallRecord, ToolResultRecord
from src.get_me_in.domain.plans import Plan, PlanItem, PlanStatus
from src.get_me_in.domain.sessions import (
    AgentSessionState,
    HandoffFrame,
    PendingToolCall,
    RuntimePhase,
    SessionState,
)


SCHEMA_VERSION = 3
_PERSISTABLE_PHASES = frozenset(
    {
        RuntimePhase.READY,
        RuntimePhase.WAITING_FOR_APPROVAL,
        RuntimePhase.WAITING_FOR_SELECTION,
        RuntimePhase.WAITING_FOR_HANDOFF,
        RuntimePhase.WAITING_FOR_USER,
        RuntimePhase.COMPLETED,
        RuntimePhase.CANCELLED,
        RuntimePhase.FAILED,
    }
)


@dataclass(frozen=True)
class SessionSnapshot:
    session: SessionState
    saved_at: datetime
    schema_version: int = SCHEMA_VERSION


class UnsupportedSessionSchemaError(ValueError):
    """The snapshot belongs to a schema this runtime deliberately does not migrate."""

    unsupported_schema = True


class SessionSnapshotCodec:
    """Encode only stable state and reject malformed or incompatible data."""

    def encode(self, snapshot: SessionSnapshot) -> dict[str, object]:
        if snapshot.schema_version != SCHEMA_VERSION:
            raise UnsupportedSessionSchemaError(
                f"Only schema_version={SCHEMA_VERSION} session snapshots are supported"
            )
        self._validate_session(snapshot.session)
        return {
            "schema_version": SCHEMA_VERSION,
            "session_id": snapshot.session.session_id,
            "active_agent": snapshot.session.active_agent.value,
            "agents": {
                key.value: self._encode_agent(state)
                for key, state in snapshot.session.agents.items()
            },
            "handoff_stack": [self._encode_frame(frame) for frame in snapshot.session.handoff_stack],
            "created_at": snapshot.session.created_at.isoformat(),
            "updated_at": snapshot.session.updated_at.isoformat(),
            "saved_at": snapshot.saved_at.isoformat(),
            "llm_attempts": [self._encode_attempt(attempt) for attempt in snapshot.session.llm_attempts],
        }

    def decode(self, payload: Mapping[str, object]) -> SessionSnapshot:
        schema_version = _schema_version(payload)
        if schema_version != SCHEMA_VERSION:
            raise UnsupportedSessionSchemaError(
                f"Session snapshot must use schema_version={SCHEMA_VERSION}"
            )
        try:
            agents_raw = _mapping(payload["agents"], "agents")
            agents = {AgentKey(key): self._decode_agent(_mapping(value, f"agents.{key}")) for key, value in agents_raw.items()}
            handoff_stack = tuple(
                self._decode_frame(_mapping(item, "handoff_stack item"))
                for item in _sequence(payload["handoff_stack"], "handoff_stack")
            )
            session = SessionState(
                session_id=_text(payload["session_id"], "session_id"),
                active_agent=AgentKey(_text(payload["active_agent"], "active_agent")),
                agents=agents,
                handoff_stack=handoff_stack,
                created_at=_time(payload["created_at"], "created_at"),
                updated_at=_time(payload["updated_at"], "updated_at"),
                llm_attempts=tuple(
                    self._decode_attempt(_mapping(item, "llm_attempts item"))
                    for item in _sequence(payload.get("llm_attempts", []), "llm_attempts")
                ),
            )
            snapshot = SessionSnapshot(session, _time(payload["saved_at"], "saved_at"))
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"Invalid session snapshot: {error}") from error
        self._validate_session(snapshot.session)
        self._validate_attempts(snapshot.session.llm_attempts)
        return snapshot

    def _validate_session(self, session: SessionState) -> None:
        if not session.session_id:
            raise ValueError("Session id must not be blank")
        if session.active_agent not in session.agents:
            raise ValueError("Active agent must have session state")
        self._validate_attempts(session.llm_attempts)
        for key, state in session.agents.items():
            if state.phase not in _PERSISTABLE_PHASES:
                raise ValueError(f"Phase {state.phase.value} cannot be restored safely")
            self._validate_agent(key, state)
        for frame in session.handoff_stack:
            if frame.source not in session.agents or frame.target not in session.agents:
                raise ValueError("Handoff frame references an unknown agent")
        if len(session.handoff_stack) > 1:
            raise ValueError("Nested handoff frames are not supported")
        if session.handoff_stack:
            frame = session.handoff_stack[-1]
            source = session.agents[frame.source]
            if session.active_agent is not frame.target:
                raise ValueError("Active agent must match the handoff target")
            if source.phase is not RuntimePhase.WAITING_FOR_HANDOFF:
                raise ValueError("Handoff source must be waiting for completion")
            if source.pending_tool is None or source.pending_tool.call_id != frame.call_id:
                raise ValueError("Handoff frame must match the source pending call")
            if source.turn_id != frame.turn_id:
                raise ValueError("Handoff frame must match the source turn")
            self._validate_inactive_subagents(session, frame.target)
        else:
            self._validate_inactive_subagents(session, None)

    @staticmethod
    def _validate_inactive_subagents(session: SessionState, active_target: AgentKey | None) -> None:
        for key, state in session.agents.items():
            if key is AgentKey.MAIN or key is active_target:
                continue
            if state != AgentSessionState():
                raise ValueError(f"Inactive SubAgent state must be empty: {key.value}")

    @staticmethod
    def _validate_agent(key: AgentKey, state: AgentSessionState) -> None:
        del key
        if state.pending_logical_call is not None:
            raise ValueError("Pending logical call is transient and cannot be persisted")
        _integer(state.format_repairs_used, "format_repairs_used")
        call_ids = {record.call_id for record in state.history if isinstance(record, ToolCallRecord)}
        result_ids = {record.call_id for record in state.history if isinstance(record, ToolResultRecord)}
        if not result_ids <= call_ids:
            raise ValueError("Tool result has no matching tool call")
        if state.pending_tool is not None and state.pending_tool.call_id not in call_ids - result_ids:
            raise ValueError("Pending tool must match one unclosed tool call")
        if state.phase in {
            RuntimePhase.WAITING_FOR_APPROVAL,
            RuntimePhase.WAITING_FOR_SELECTION,
            RuntimePhase.WAITING_FOR_HANDOFF,
        } and state.pending_tool is None:
            raise ValueError("Waiting phase requires a pending tool call")

    def _encode_agent(self, state: AgentSessionState) -> dict[str, object]:
        return {
            "phase": state.phase.value,
            "history": [self._encode_record(record) for record in state.history],
            "turn_id": state.turn_id,
            "model_calls": state.model_calls,
            "pending_tool": None if state.pending_tool is None else {
                "call_id": state.pending_tool.call_id,
                "tool_name": state.pending_tool.tool_name,
                "arguments": dict(state.pending_tool.arguments),
            },
            "format_repairs_used": state.format_repairs_used,
            "repair_attempted": state.format_repairs_used > 0,
            "cancel_reason": state.cancel_reason,
            "plan": self._encode_plan(state.plan),
        }

    def _decode_agent(self, payload: Mapping[str, object]) -> AgentSessionState:
        if payload.get("pending_logical_call") is not None:
            raise ValueError("Pending logical call is transient and cannot be restored")
        pending_raw = payload.get("pending_tool")
        pending = None if pending_raw is None else PendingToolCall(
            _text(_mapping(pending_raw, "pending_tool")["call_id"], "pending_tool.call_id"),
            _text(_mapping(pending_raw, "pending_tool")["tool_name"], "pending_tool.tool_name"),
            _mapping(_mapping(pending_raw, "pending_tool")["arguments"], "pending_tool.arguments"),
        )
        format_repairs_used = _decode_format_repairs(payload)
        return AgentSessionState(
            phase=RuntimePhase(_text(payload["phase"], "phase")),
            history=tuple(self._decode_record(_mapping(item, "history item")) for item in _sequence(payload["history"], "history")),
            turn_id=_string(payload["turn_id"], "turn_id"),
            model_calls=_integer(payload["model_calls"], "model_calls"),
            pending_tool=pending,
            format_repairs_used=format_repairs_used,
            cancel_reason=_text(payload["cancel_reason"], "cancel_reason"),
            plan=self._decode_plan(payload.get("plan")),
        )

    @staticmethod
    def _encode_attempt(attempt: LLMAttemptRecord) -> dict[str, object]:
        usage: dict[str, object]
        if isinstance(attempt.usage, ReportedUsage):
            usage = {
                "status": "reported",
                "input_tokens": attempt.usage.value.input_tokens,
                "output_tokens": attempt.usage.value.output_tokens,
                "cached_input_tokens": attempt.usage.value.cached_input_tokens,
                "reasoning_output_tokens": attempt.usage.value.reasoning_output_tokens,
            }
        else:
            usage = {"status": "unavailable", "reason": attempt.usage.reason.value}
        if isinstance(attempt.cost, EstimatedCost):
            cost: dict[str, object] = {
                "status": "estimated",
                "amount": format(attempt.cost.amount, "f"),
                "unit": attempt.cost.unit,
                "basis": attempt.cost.basis.value,
            }
        else:
            cost = {"status": "unavailable", "reason": attempt.cost.reason.value}
        return {
            "attempt_id": attempt.attempt_id,
            "logical_call_id": attempt.logical_call_id,
            "attempt_index": attempt.attempt_index,
            "scope": {
                "agent": attempt.scope.agent.value,
                "turn_id": attempt.scope.turn_id,
                "purpose": attempt.scope.purpose.value,
                "handoff_episode_id": attempt.scope.handoff_episode_id,
            },
            "reason": attempt.reason.value,
            "request_profile": attempt.request_profile.value,
            "response_model": attempt.response_model,
            "outcome": attempt.outcome.value,
            "usage": usage,
            "cost": cost,
            "terminal_at": attempt.terminal_at.isoformat(),
        }

    @staticmethod
    def _decode_attempt(payload: Mapping[str, object]) -> LLMAttemptRecord:
        _exact_keys(
            payload,
            {
                "attempt_id", "logical_call_id", "attempt_index", "scope", "reason",
                "request_profile", "response_model", "outcome", "usage", "cost", "terminal_at",
            },
            "llm_attempts item",
        )
        scope_payload = _mapping(payload["scope"], "scope")
        _exact_keys(scope_payload, {"agent", "turn_id", "purpose", "handoff_episode_id"}, "scope")
        scope = LLMAttemptScope(
            agent=AgentKey(_text(scope_payload["agent"], "scope.agent")),
            turn_id=_text(scope_payload["turn_id"], "scope.turn_id"),
            purpose=LLMAttemptPurpose(_text(scope_payload["purpose"], "scope.purpose")),
            handoff_episode_id=_optional_text(scope_payload["handoff_episode_id"], "scope.handoff_episode_id"),
        )
        usage_payload = _mapping(payload["usage"], "usage")
        usage_status = _text(usage_payload.get("status"), "usage.status")
        if usage_status == "reported":
            _exact_keys(
                usage_payload,
                {"status", "input_tokens", "output_tokens", "cached_input_tokens", "reasoning_output_tokens"},
                "usage",
            )
            usage = ReportedUsage(
                TokenUsage(
                    input_tokens=_integer(usage_payload["input_tokens"], "usage.input_tokens"),
                    output_tokens=_integer(usage_payload["output_tokens"], "usage.output_tokens"),
                    cached_input_tokens=_optional_integer(usage_payload["cached_input_tokens"], "usage.cached_input_tokens"),
                    reasoning_output_tokens=_optional_integer(usage_payload["reasoning_output_tokens"], "usage.reasoning_output_tokens"),
                )
            )
        elif usage_status == "unavailable":
            _exact_keys(usage_payload, {"status", "reason"}, "usage")
            usage = UnavailableUsage(
                UsageUnavailableReason(_text(usage_payload["reason"], "usage.reason"))
            )
        else:
            raise ValueError(f"Unknown usage status: {usage_status}")

        cost_payload = _mapping(payload["cost"], "cost")
        cost_status = _text(cost_payload.get("status"), "cost.status")
        if cost_status == "estimated":
            _exact_keys(cost_payload, {"status", "amount", "unit", "basis"}, "cost")
            cost = EstimatedCost(
                _decimal(cost_payload["amount"], "cost.amount"),
                _text(cost_payload["unit"], "cost.unit"),
                CostEstimateBasis(_text(cost_payload["basis"], "cost.basis")),
            )
        elif cost_status == "unavailable":
            _exact_keys(cost_payload, {"status", "reason"}, "cost")
            cost = CostUnavailable(
                CostUnavailableReason(_text(cost_payload["reason"], "cost.reason"))
            )
        else:
            raise ValueError(f"Unknown cost status: {cost_status}")

        return LLMAttemptRecord(
            attempt_id=_text(payload["attempt_id"], "attempt_id"),
            logical_call_id=_text(payload["logical_call_id"], "logical_call_id"),
            attempt_index=_positive_integer(payload["attempt_index"], "attempt_index"),
            scope=scope,
            reason=LLMAttemptReason(_text(payload["reason"], "reason")),
            request_profile=ModelProfile(_text(payload["request_profile"], "request_profile")),
            response_model=_optional_text(payload["response_model"], "response_model"),
            outcome=LLMAttemptOutcome(_text(payload["outcome"], "outcome")),
            usage=usage,
            cost=cost,
            terminal_at=_time(payload["terminal_at"], "terminal_at"),
        )

    @staticmethod
    def _validate_attempts(attempts: tuple[LLMAttemptRecord, ...]) -> None:
        attempt_ids: set[str] = set()
        logical_indexes: set[tuple[str, int]] = set()
        grouped: dict[str, list[LLMAttemptRecord]] = {}
        units: set[str] = set()
        for attempt in attempts:
            if attempt.attempt_id in attempt_ids:
                raise ValueError("Duplicate LLM attempt id")
            key = (attempt.logical_call_id, attempt.attempt_index)
            if key in logical_indexes:
                raise ValueError("Duplicate logical call attempt index")
            attempt_ids.add(attempt.attempt_id)
            logical_indexes.add(key)
            grouped.setdefault(attempt.logical_call_id, []).append(attempt)
            if isinstance(attempt.cost, EstimatedCost):
                units.add(attempt.cost.unit)
        if len(units) > 1:
            raise ValueError("All estimated costs must use one billing unit")
        for logical_call_id, group in grouped.items():
            ordered = sorted(group, key=lambda item: item.attempt_index)
            for expected_index, attempt in enumerate(ordered, start=1):
                if attempt.attempt_index != expected_index:
                    raise ValueError(f"Attempt indexes for {logical_call_id} must be contiguous")
                if expected_index == 1 and attempt.reason.value != "primary":
                    raise ValueError("The first attempt of a logical call must be PRIMARY")
                if expected_index > 1 and attempt.reason.value == "primary":
                    raise ValueError("PRIMARY may only be used for the first attempt")
            first = ordered[0]
            for attempt in ordered[1:]:
                if attempt.scope != first.scope or attempt.request_profile != first.request_profile:
                    raise ValueError("Logical call scope and profile must remain stable")

    @staticmethod
    def _encode_record(record: MessageRecord | ToolCallRecord | ToolResultRecord) -> dict[str, object]:
        base = {"event_id": record.event_id, "timestamp": record.timestamp.isoformat(), "turn_id": record.turn_id}
        if isinstance(record, MessageRecord):
            payload = {**base, "kind": "message", "role": record.role.value, "content": record.content}
            if record.role is Role.ASSISTANT and record.thinking is not None:
                payload["thinking"] = record.thinking
            if record.plan is not None:
                payload["plan"] = SessionSnapshotCodec._encode_plan(record.plan)
            return payload
        if isinstance(record, ToolCallRecord):
            payload = {**base, "kind": "tool_call", "call_id": record.call_id, "tool_name": record.tool_name, "arguments": dict(record.arguments), "content": record.content}
            if record.thinking is not None:
                payload["thinking"] = record.thinking
            if record.plan is not None:
                payload["plan"] = SessionSnapshotCodec._encode_plan(record.plan)
            return payload
        payload = {**base, "kind": "tool_result", "call_id": record.call_id, "tool_name": record.tool_name, "output": record.output}
        if record.plan is not None:
            payload["plan"] = SessionSnapshotCodec._encode_plan(record.plan)
        return payload

    @staticmethod
    def _decode_record(payload: Mapping[str, object]) -> MessageRecord | ToolCallRecord | ToolResultRecord:
        common = (_text(payload["event_id"], "event_id"), _time(payload["timestamp"], "timestamp"), _text(payload["turn_id"], "turn_id"))
        kind = _text(payload["kind"], "kind")
        if kind == "message":
            role = Role(_text(payload["role"], "role"))
            thinking = _optional_thinking(payload) if role is Role.ASSISTANT else None
            if role is not Role.ASSISTANT and "thinking" in payload:
                raise ValueError("Only assistant messages may contain thinking")
            return MessageRecord(common[0], role, _text(payload["content"], "content"), common[1], common[2], thinking, SessionSnapshotCodec._decode_plan(payload.get("plan")))
        if kind == "tool_call":
            return ToolCallRecord(common[0], _text(payload["call_id"], "call_id"), _text(payload["tool_name"], "tool_name"), _mapping(payload["arguments"], "arguments"), common[1], common[2], _optional_thinking(payload), SessionSnapshotCodec._decode_plan(payload.get("plan")), _string(payload.get("content", ""), "content"))
        if kind == "tool_result":
            return ToolResultRecord(common[0], _text(payload["call_id"], "call_id"), _text(payload["tool_name"], "tool_name"), payload["output"], common[1], common[2], SessionSnapshotCodec._decode_plan(payload.get("plan")))
        raise ValueError(f"Unknown conversation record kind: {kind}")

    @staticmethod
    def _encode_plan(plan: Plan | None) -> dict[str, object] | None:
        if plan is None:
            return None
        return {"plan_id": plan.plan_id, "items": [{"item_id": item.item_id, "description": item.description, "status": item.status.value} for item in plan.items]}

    @staticmethod
    def _decode_plan(raw: object) -> Plan | None:
        if raw is None:
            return None
        payload = _mapping(raw, "plan")
        return Plan(_text(payload["plan_id"], "plan_id"), tuple(PlanItem(_text(_mapping(item, "plan item")["item_id"], "plan item.item_id"), _text(_mapping(item, "plan item")["description"], "plan item.description"), PlanStatus(_text(_mapping(item, "plan item")["status"], "plan item.status"))) for item in _sequence(payload["items"], "plan.items")))

    @staticmethod
    def _encode_frame(frame: HandoffFrame) -> dict[str, object]:
        return {"source": frame.source.value, "target": frame.target.value, "call_id": frame.call_id, "turn_id": frame.turn_id, "context": frame.context}

    @staticmethod
    def _decode_frame(payload: Mapping[str, object]) -> HandoffFrame:
        return HandoffFrame(AgentKey(_text(payload["source"], "source")), AgentKey(_text(payload["target"], "target")), _text(payload["call_id"], "call_id"), _text(payload["turn_id"], "turn_id"), _text(payload["context"], "context"))


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be an object")
    return value


def _exact_keys(payload: Mapping[str, object], expected: set[str], label: str) -> None:
    actual = set(payload)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ValueError(f"{label} has invalid keys: missing={missing}, extra={extra}")


def _schema_version(payload: Mapping[str, object]) -> int:
    try:
        value = payload["schema_version"]
    except KeyError as error:
        raise ValueError("schema_version is required") from error
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError("schema_version must be a non-negative integer")
    return value


def _sequence(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise TypeError(f"{label} must be an array")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise TypeError(f"{label} must be a non-empty string")
    return value


def _optional_text(value: object, label: str) -> str | None:
    if value is None:
        return None
    return _text(value, label)


def _string(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string")
    return value


def _integer(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise TypeError(f"{label} must be a non-negative integer")
    return value


def _positive_integer(value: object, label: str) -> int:
    result = _integer(value, label)
    if result < 1:
        raise ValueError(f"{label} must be a positive integer")
    return result


def _optional_integer(value: object, label: str) -> int | None:
    if value is None:
        return None
    return _integer(value, label)


def _decimal(value: object, label: str) -> Decimal:
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f"{label} must be a decimal string")
    try:
        return Decimal(value)
    except InvalidOperation as error:
        raise ValueError(f"{label} must be a decimal string") from error


def _boolean(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{label} must be a boolean")
    return value


def _decode_format_repairs(payload: Mapping[str, object]) -> int:
    if "format_repairs_used" in payload:
        return _integer(payload["format_repairs_used"], "format_repairs_used")
    if "repair_attempted" in payload:
        return int(_boolean(payload["repair_attempted"], "repair_attempted"))
    return 0


def _optional_thinking(payload: Mapping[str, object]) -> str | None:
    thinking = payload.get("thinking")
    if thinking is not None and not isinstance(thinking, str):
        raise TypeError("thinking must be a string when present")
    return thinking


def _time(value: object, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(_text(value, label))
    except ValueError as error:
        raise ValueError(f"{label} must be an ISO-8601 datetime") from error
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must include a timezone")
    return parsed
