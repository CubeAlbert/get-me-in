"""Parsing of the strict JSON response expected from a model."""

import json
from dataclasses import dataclass
from typing import Any


class ModelReplyParseError(ValueError):
    """Raised when a model response does not satisfy the R2 reply contract."""


@dataclass(frozen=True)
class ModelReply:
    """The provider-neutral result consumed by ``AgentRuntime``."""

    content: str
    thinking: str = ""
    tool_name: str | None = None
    tool_arguments: dict[str, Any] | None = None


class ModelReplyParser:
    """Parses R2 JSON replies without exposing provider data to domain code."""

    def parse(self, raw: str) -> ModelReply:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as error:
            raise ModelReplyParseError("Model response is not valid JSON") from error
        if not isinstance(payload, dict):
            raise ModelReplyParseError("Model response must be a JSON object")

        content = payload.get("content")
        if not isinstance(content, str):
            raise ModelReplyParseError("Model response requires string content")

        thinking = payload.get("thinking", "")
        if not isinstance(thinking, str):
            raise ModelReplyParseError("thinking must be a string")

        tool_call = payload.get("tool_call")
        if tool_call is None:
            return ModelReply(content=content, thinking=thinking)
        if not isinstance(tool_call, dict):
            raise ModelReplyParseError("tool_call must be an object")
        name = tool_call.get("name")
        arguments = tool_call.get("arguments", {})
        if not isinstance(name, str) or not name:
            raise ModelReplyParseError("tool_call requires a non-empty name")
        if not isinstance(arguments, dict):
            raise ModelReplyParseError("tool_call arguments must be an object")
        return ModelReply(
            content=content,
            thinking=thinking,
            tool_name=name,
            tool_arguments=arguments,
        )
