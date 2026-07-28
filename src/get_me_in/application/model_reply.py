"""Parsing of the strict JSON response expected from a model."""

import json
from dataclasses import dataclass
from typing import Any

import json_repair


class ModelReplyParseError(ValueError):
    """Raised when a model response does not satisfy the R2 reply contract."""


@dataclass(frozen=True)
class ModelReply:
    """The provider-neutral result consumed by ``AgentRuntime``."""

    content: str
    thinking: str | None = None
    tool_name: str | None = None
    tool_arguments: dict[str, Any] | None = None
    repair_kind: str | None = None


class ModelReplyParser:
    """Parse the single minimal model-output contract into domain-neutral data."""

    def parse(self, raw: str) -> ModelReply:
        try:
            payload = json.loads(raw)
            repair_kind = None
        except json.JSONDecodeError:
            try:
                payload = json_repair.loads(raw)
            except Exception as error:
                raise ModelReplyParseError("Model response could not be repaired") from error
            repair_kind = "json_repair"
        if not isinstance(payload, dict):
            raise ModelReplyParseError("Model response must be a JSON object")

        event_type = payload.get("event_type")
        if event_type not in {"finish", "tool_call"}:
            raise ModelReplyParseError("event_type must be finish or tool_call")

        content = payload.get("message")
        if not isinstance(content, str):
            raise ModelReplyParseError("message must be a string")

        if event_type == "finish":
            if not content.strip():
                raise ModelReplyParseError("finish message must be non-empty")
            if "thinking" not in payload:
                raise ModelReplyParseError("finish requires a string thinking field")
            thinking = payload["thinking"]
            if not isinstance(thinking, str):
                raise ModelReplyParseError("thinking must be a string")
            if payload.get("tool") is not None:
                raise ModelReplyParseError("finish tool must be null or omitted")
            if payload.get("event_payload") is not None:
                raise ModelReplyParseError("finish event_payload must be null or omitted")
            return ModelReply(
                content=content,
                thinking=thinking,
                repair_kind=repair_kind,
            )

        thinking = payload.get("thinking")
        if "thinking" in payload and not isinstance(thinking, str):
            raise ModelReplyParseError("thinking must be a string")
        name = payload.get("tool")
        arguments = payload.get("event_payload")
        if not isinstance(name, str) or not name.strip():
            raise ModelReplyParseError("tool_call requires a non-empty tool")
        if not isinstance(arguments, dict):
            raise ModelReplyParseError("tool_call event_payload must be an object")
        return ModelReply(
            content=content,
            thinking=thinking,
            tool_name=name,
            tool_arguments=arguments,
            repair_kind=repair_kind,
        )
