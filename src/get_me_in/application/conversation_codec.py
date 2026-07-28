"""Encode domain conversation records for the retained static prompt contract."""

import json
from collections.abc import Iterable

from src.get_me_in.domain.messages import (
    ConversationRecord,
    MessageRecord,
    Role,
    ToolCallRecord,
    ToolResultRecord,
)
from src.get_me_in.domain.plans import Plan, PlanStatus
from src.get_me_in.ports.llm import LLMMessage


class ConversationCodec:
    """Maps strong domain records to provider-neutral prompt messages."""

    def encode(
        self,
        system_prompt: str,
        records: Iterable[ConversationRecord],
    ) -> tuple[LLMMessage, ...]:
        return (
            LLMMessage(Role.SYSTEM, system_prompt),
            *(self._encode_record(record) for record in records),
        )

    @staticmethod
    def _encode_record(record: ConversationRecord) -> LLMMessage:
        if isinstance(record, MessageRecord):
            event_type = {
                Role.USER: "user_input",
                Role.SYSTEM: "system_message",
                Role.ASSISTANT: "finish",
            }[record.role]
            payload = {
                "id": record.event_id,
                "role": record.role.value,
                "timestamp": record.timestamp.isoformat(),
                "event_type": event_type,
                "message": record.content,
                "tool": None,
                "tool_call_id": None,
                "event_payload": None,
                "plan_status": _plan_status(record.plan),
            }
            role = record.role
        elif isinstance(record, ToolCallRecord):
            payload = {
                "id": record.event_id,
                "role": Role.ASSISTANT.value,
                "timestamp": record.timestamp.isoformat(),
                "event_type": "tool_call",
                "message": record.content,
                "tool": record.tool_name,
                "tool_call_id": record.call_id,
                "event_payload": dict(record.arguments),
                "plan_status": _plan_status(record.plan),
            }
            role = Role.ASSISTANT
        else:
            assert isinstance(record, ToolResultRecord)
            output = record.output
            message = output if isinstance(output, str) else ""
            event_payload = output if not isinstance(output, str) else {"result": output}
            payload = {
                "id": record.event_id,
                "role": Role.USER.value,
                "timestamp": record.timestamp.isoformat(),
                "event_type": "tool_call_result",
                "message": message,
                "tool": record.tool_name,
                "tool_call_id": record.call_id,
                "event_payload": event_payload,
                "plan_status": _plan_status(record.plan),
            }
            role = Role.USER
        return LLMMessage(role, json.dumps(payload, ensure_ascii=False, sort_keys=True))


def _plan_status(plan: Plan | None) -> dict[str, object] | None:
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
    return {
        "current": current,
        "completed": completed,
        "remaining": remaining,
    }
