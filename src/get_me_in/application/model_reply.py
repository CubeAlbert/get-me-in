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

        removed_fields = {"event_type", "tool", "event_payload", "content"}
        if removed_fields.intersection(payload):
            raise ModelReplyParseError(
                "Model response must use only the message/thinking/tool_call envelope"
            )

        content = payload.get("message")
        if not isinstance(content, str):
            raise ModelReplyParseError("message must be a string")

        tool_call = payload.get("tool_call")
        thinking = payload.get("thinking")
        if thinking is not None and not isinstance(thinking, str):
            raise ModelReplyParseError("thinking must be a string")

        if tool_call is None:
            if not content.strip():
                raise ModelReplyParseError("finish message must be non-empty")
            return ModelReply(
                content=content,
                thinking=thinking,
                repair_kind=repair_kind,
            )

        if not isinstance(tool_call, dict):
            raise ModelReplyParseError("tool_call must be an object or null")
        name = tool_call.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ModelReplyParseError("tool_call requires a non-empty name")
        arguments = tool_call.get("arguments")
        if arguments is None:
            arguments = {}
        if not isinstance(arguments, dict):
            raise ModelReplyParseError("tool_call arguments must be an object")
        return ModelReply(
            content=content,
            thinking=thinking,
            tool_name=name,
            tool_arguments=arguments,
            repair_kind=repair_kind,
        )
