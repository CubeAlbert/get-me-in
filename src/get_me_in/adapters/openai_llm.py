"""OpenAI SDK adapter with request-scoped, cancellable clients."""

from collections.abc import Callable, Mapping
from math import isfinite

from openai import OpenAI

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
            response = client.chat.completions.create(**create_kwargs)
            if cancellation.is_cancelled:
                raise InterruptedError("Model completion was cancelled")
            content = response.choices[0].message.content
            if content is None:
                raise RuntimeError("Model completion did not contain content")
            return LLMResult(content=content)
        finally:
            registration.close()
            client.close()

    def close(self) -> None:
        self._closed = True
