"""The single provider-facing message entity and its two directional projections."""

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Any

import json_repair

from src.get_me_in.domain.messages import (
    ConversationRecord,
    MessageRecord,
    Role,
    ToolCallRecord,
    ToolResultRecord,
)
from src.get_me_in.domain.plans import Plan, PlanStatus
from src.get_me_in.ports.llm import LLMMessage


class ModelMessageEventType(StrEnum):
    """Events represented by the shared model-message entity."""

    USER_INPUT = "user_input"
    TOOL_CALL_RESULT = "tool_call_result"
    SYSTEM_MESSAGE = "system_message"
    TOOL_CALL = "tool_call"
    FINISH = "finish"


class ModelMessageParseError(ValueError):
    """Raised when a model reply cannot be projected into the entity."""


@dataclass(frozen=True)
class ModelMessageEntity:
    """Immutable carrier used for both history input and model output projections."""

    id: str | None
    role: Role | None
    timestamp: datetime | None
    event_type: ModelMessageEventType
    message: str
    tool: str | None = None
    tool_call_id: str | None = None
    event_payload: Mapping[str, object] | None = None
    thinking: str | None = None
    plan_status: Mapping[str, object] | None = None
    repair_kind: str | None = None

    def __post_init__(self) -> None:
        if self.event_payload is not None and not isinstance(self.event_payload, Mapping):
            raise TypeError("event_payload must be a mapping or None")
        if self.plan_status is not None and not isinstance(self.plan_status, Mapping):
            raise TypeError("plan_status must be a mapping or None")

    @classmethod
    def from_output(
        cls,
        *,
        event_type: ModelMessageEventType,
        message: str,
        tool: str | None = None,
        event_payload: Mapping[str, object] | None = None,
        thinking: str | None = None,
        repair_kind: str | None = None,
    ) -> "ModelMessageEntity":
        return cls(
            id=None,
            role=None,
            timestamp=None,
            event_type=event_type,
            message=message,
            tool=tool,
            tool_call_id=None,
            event_payload=_freeze(event_payload),
            thinking=thinking,
            plan_status=None,
            repair_kind=repair_kind,
        )

    def input_payload(self) -> dict[str, object]:
        """Return the complete InputFormat history projection."""
        if self.id is None or self.role is None or self.timestamp is None:
            raise ValueError("InputFormat projection requires id, role, and timestamp")
        return {
            "id": self.id,
            "role": self.role.value,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "message": self.message,
            "tool": self.tool,
            "tool_call_id": self.tool_call_id,
            "event_payload": _thaw(self.event_payload),
            "plan_status": _thaw(self.plan_status),
        }


class ModelMessageCodec:
    """Encode conversation history and parse flat model replies."""

    _OUTPUT_FIELDS = frozenset(
        {"event_type", "message", "thinking", "tool", "event_payload"}
    )

    def encode(
        self,
        system_prompt: str,
        records: Iterable[ConversationRecord],
    ) -> tuple[LLMMessage, ...]:
        return (
            LLMMessage(Role.SYSTEM, system_prompt),
            *(self._encode_record(record) for record in records),
        )

    def parse(self, raw: str) -> ModelMessageEntity:
        try:
            payload = json.loads(raw)
            repair_kind = None
        except json.JSONDecodeError:
            try:
                payload = json_repair.loads(raw)
            except Exception as error:
                raise ModelMessageParseError(
                    "Model response could not be repaired"
                ) from error
            repair_kind = "json_repair"

        if not isinstance(payload, dict):
            raise ModelMessageParseError("Model response must be a JSON object")

        event_type = payload.get("event_type")
        if not isinstance(event_type, str):
            raise ModelMessageParseError("event_type must be a string")
        try:
            event = ModelMessageEventType(event_type)
        except ValueError as error:
            raise ModelMessageParseError(
                "event_type must be finish or tool_call"
            ) from error
        if event not in {
            ModelMessageEventType.FINISH,
            ModelMessageEventType.TOOL_CALL,
        }:
            raise ModelMessageParseError("event_type must be finish or tool_call")

        message = payload.get("message")
        if not isinstance(message, str):
            raise ModelMessageParseError("message must be a string")

        thinking = payload.get("thinking")
        if thinking is not None and not isinstance(thinking, str):
            raise ModelMessageParseError("thinking must be a string")

        if event is ModelMessageEventType.FINISH:
            if not message.strip():
                raise ModelMessageParseError("finish message must be non-empty")
            if payload.get("tool") is not None:
                raise ModelMessageParseError("finish tool must be null or omitted")
            if payload.get("event_payload") is not None:
                raise ModelMessageParseError(
                    "finish event_payload must be null or omitted"
                )
            return ModelMessageEntity.from_output(
                event_type=event,
                message=message,
                thinking=thinking,
                repair_kind=repair_kind,
            )

        tool = payload.get("tool")
        if not isinstance(tool, str) or not tool.strip():
            raise ModelMessageParseError(
                "tool_call requires a non-empty tool string"
            )
        event_payload = payload.get("event_payload")
        if not isinstance(event_payload, dict):
            raise ModelMessageParseError("tool_call event_payload must be an object")
        return ModelMessageEntity.from_output(
            event_type=event,
            message=message,
            tool=tool,
            event_payload=event_payload,
            thinking=thinking,
            repair_kind=repair_kind,
        )

    @classmethod
    def _encode_record(cls, record: ConversationRecord) -> LLMMessage:
        if isinstance(record, MessageRecord):
            event_type = {
                Role.USER: ModelMessageEventType.USER_INPUT,
                Role.SYSTEM: ModelMessageEventType.SYSTEM_MESSAGE,
                Role.ASSISTANT: ModelMessageEventType.FINISH,
            }[record.role]
            entity = ModelMessageEntity(
                id=record.event_id,
                role=record.role,
                timestamp=record.timestamp,
                event_type=event_type,
                message=record.content,
                plan_status=_freeze_plan(record.plan),
            )
        elif isinstance(record, ToolCallRecord):
            entity = ModelMessageEntity(
                id=record.event_id,
                role=Role.ASSISTANT,
                timestamp=record.timestamp,
                event_type=ModelMessageEventType.TOOL_CALL,
                message=record.content,
                tool=record.tool_name,
                tool_call_id=record.call_id,
                event_payload=_freeze(record.arguments),
                plan_status=_freeze_plan(record.plan),
            )
        else:
            assert isinstance(record, ToolResultRecord)
            output = record.output
            message = output if isinstance(output, str) else ""
            event_payload = output if not isinstance(output, str) else {"result": output}
            entity = ModelMessageEntity(
                id=record.event_id,
                role=Role.USER,
                timestamp=record.timestamp,
                event_type=ModelMessageEventType.TOOL_CALL_RESULT,
                message=message,
                tool=record.tool_name,
                tool_call_id=record.call_id,
                event_payload=_freeze(event_payload),
                plan_status=_freeze_plan(record.plan),
            )
        return LLMMessage(
            entity.role or Role.USER,
            json.dumps(entity.input_payload(), ensure_ascii=False, sort_keys=True),
        )


def thaw_model_value(value: object) -> Any:
    """Convert an entity mapping back to mutable tool arguments."""
    return _thaw(value)


def _freeze(value: Mapping[str, object] | None) -> Mapping[str, object] | None:
    if value is None:
        return None
    return MappingProxyType({str(key): _freeze_value(item) for key, item in value.items()})


def _freeze_value(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _freeze_value(item) for key, item in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_value(item) for item in value)
    return value


def _thaw(value: object) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


def _freeze_plan(plan: Plan | None) -> Mapping[str, object] | None:
    if plan is None:
        return None
    current: str | None = None
    completed: list[str] = []
    remaining: list[str] = []
    for index, item in enumerate(plan.items):
        label = f"{index}|{item.description}"
        if item.status is PlanStatus.IN_PROGRESS:
            current = label
        elif item.status is PlanStatus.COMPLETED:
            completed.append(label)
        elif item.status is PlanStatus.PENDING:
            remaining.append(label)
    if current is None and not remaining:
        return None
    return _freeze(
        {
            "current": current,
            "completed": completed,
            "remaining": remaining,
        }
    )
