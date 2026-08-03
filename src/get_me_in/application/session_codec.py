"""Disk-safe codec for session snapshots, separate from model conversation codec."""

from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import datetime

from src.get_me_in.domain.agents import AgentKey
from src.get_me_in.domain.messages import MessageRecord, Role, ToolCallRecord, ToolResultRecord
from src.get_me_in.domain.plans import Plan, PlanItem, PlanStatus
from src.get_me_in.domain.sessions import (
    AgentSessionState,
    HandoffFrame,
    PendingToolCall,
    RuntimePhase,
    SessionState,
)


SCHEMA_VERSION = 2
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


class SessionSnapshotCodec:
    """Encode only stable state and reject malformed or incompatible data."""

    def encode(self, snapshot: SessionSnapshot) -> dict[str, object]:
        if snapshot.schema_version != SCHEMA_VERSION:
            raise ValueError("Only schema_version=2 session snapshots are supported")
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
        }

    def decode(self, payload: Mapping[str, object]) -> SessionSnapshot:
        if payload.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("Session snapshot must use schema_version=2")
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
            )
            if handoff_stack:
                frame = handoff_stack[-1]
                source_payload = _mapping(agents_raw[frame.source.value], f"agents.{frame.source.value}")
                source_state = session.agents[frame.source]
                if "turn_id" not in source_payload and not source_state.turn_id:
                    repaired_agents = dict(session.agents)
                    repaired_agents[frame.source] = replace(source_state, turn_id=frame.turn_id)
                    session = replace(session, agents=repaired_agents)
            snapshot = SessionSnapshot(session, _time(payload["saved_at"], "saved_at"))
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"Invalid session snapshot: {error}") from error
        self._validate_session(snapshot.session)
        return snapshot

    def _validate_session(self, session: SessionState) -> None:
        if not session.session_id:
            raise ValueError("Session id must not be blank")
        if session.active_agent not in session.agents:
            raise ValueError("Active agent must have session state")
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

    @staticmethod
    def _validate_agent(key: AgentKey, state: AgentSessionState) -> None:
        del key
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
            turn_id=_string(payload.get("turn_id", ""), "turn_id"),
            model_calls=_integer(payload["model_calls"], "model_calls"),
            pending_tool=pending,
            format_repairs_used=format_repairs_used,
            cancel_reason=_text(payload["cancel_reason"], "cancel_reason"),
            plan=self._decode_plan(payload.get("plan")),
        )

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


def _sequence(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise TypeError(f"{label} must be an array")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise TypeError(f"{label} must be a non-empty string")
    return value


def _string(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string")
    return value


def _integer(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise TypeError(f"{label} must be a non-negative integer")
    return value


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
