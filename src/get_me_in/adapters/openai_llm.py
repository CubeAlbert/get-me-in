"""OpenAI SDK adapter with request-scoped, cancellable clients."""

from collections.abc import Callable, Mapping
from math import isfinite

from openai import APITimeoutError, OpenAI

from src.get_me_in.domain.llm_usage import (
    ReportedUsage,
    TokenUsage,
    UnavailableUsage,
    UsageUnavailableReason,
)
from src.get_me_in.ports.llm import CancellationSignal, LLMPort, LLMRequest, LLMResult, ModelProfile


class OpenAILLMAdapter(LLMPort):
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model_names: Mapping[ModelProfile, str],
        thinking_enabled: bool,
        client_factory: Callable[[], OpenAI] | None = None,
    ) -> None:
        self._client_factory = client_factory or (
            lambda: OpenAI(api_key=api_key, base_url=base_url)
        )
        self._model_names = dict(model_names)
        self._thinking_enabled = thinking_enabled
        self._closed = False

    def complete(
        self,
        request: LLMRequest,
        cancellation: CancellationSignal,
    ) -> LLMResult:
        if self._closed:
            raise RuntimeError("OpenAILLMAdapter is closed")
        if cancellation.is_cancelled:
            raise InterruptedError("Model completion was cancelled")
        if request.temperature is not None and (
            not isfinite(request.temperature) or not 0 <= request.temperature <= 2
        ):
            raise ValueError("LLM request temperature must be a finite value between 0 and 2")

        client = self._client_factory()
        registration = cancellation.register(client.close)
        try:
            create_kwargs = {
                "model": self._model_names[request.profile],
                "messages": [
                    {"role": message.role.value, "content": message.content}
                    for message in request.messages
                ],
                "timeout": request.timeout_seconds,
                "response_format": {"type": "json_object"},
            }
            if request.temperature is not None:
                create_kwargs["temperature"] = request.temperature
            if not self._thinking_enabled:
                create_kwargs["extra_body"] = {"thinking": {"type": "disabled"}}
            try:
                response = client.chat.completions.create(**create_kwargs)
            except APITimeoutError as error:
                raise TimeoutError("Model completion timed out") from error
            content = response.choices[0].message.content
            response_model = getattr(response, "model", None)
            if not isinstance(response_model, str) or not response_model.strip():
                response_model = None
            return LLMResult(
                content=content,
                response_model=response_model,
                usage=_normalize_usage(getattr(response, "usage", None)),
            )
        finally:
            registration.close()
            client.close()

    def close(self) -> None:
        self._closed = True


_MISSING = object()


def _field(value: object, name: str) -> object:
    if isinstance(value, Mapping):
        return value.get(name, _MISSING)
    return getattr(value, name, _MISSING)


def _normalize_usage(raw: object) -> ReportedUsage | UnavailableUsage:
    if raw is None:
        return UnavailableUsage(UsageUnavailableReason.NOT_REPORTED)
    prompt = _field(raw, "prompt_tokens")
    completion = _field(raw, "completion_tokens")
    total = _field(raw, "total_tokens")
    if _MISSING in (prompt, completion, total):
        return UnavailableUsage(UsageUnavailableReason.NOT_REPORTED)
    if not all(_valid_token(value) for value in (prompt, completion, total)):
        return UnavailableUsage(UsageUnavailableReason.MALFORMED)
    if total != prompt + completion:
        return UnavailableUsage(UsageUnavailableReason.MALFORMED)

    prompt_details = _field(raw, "prompt_tokens_details")
    completion_details = _field(raw, "completion_tokens_details")
    cached = _optional_token(prompt_details, "cached_tokens")
    reasoning = _optional_token(completion_details, "reasoning_tokens")
    if cached is _MISSING or reasoning is _MISSING:
        return UnavailableUsage(UsageUnavailableReason.MALFORMED)
    try:
        return ReportedUsage(
            TokenUsage(
                input_tokens=prompt,
                output_tokens=completion,
                cached_input_tokens=cached,
                reasoning_output_tokens=reasoning,
            )
        )
    except ValueError:
        return UnavailableUsage(UsageUnavailableReason.MALFORMED)


def _optional_token(container: object, name: str) -> int | None | object:
    if container is None or container is _MISSING:
        return None
    value = _field(container, name)
    if value is _MISSING or value is None:
        return None
    if not _valid_token(value):
        return _MISSING
    return value


def _valid_token(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0
