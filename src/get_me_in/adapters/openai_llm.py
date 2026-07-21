"""OpenAI SDK adapter for the v2 provider-neutral LLM port."""

from collections.abc import Mapping

from openai import OpenAI

from src.get_me_in.ports.llm import CancellationSignal, LLMPort, LLMRequest, LLMResult, ModelProfile


class OpenAILLMAdapter(LLMPort):
    """Synchronous adapter using only public OpenAI SDK lifecycle APIs."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model_names: Mapping[ModelProfile, str],
        thinking_enabled: bool,
        client: OpenAI | None = None,
    ) -> None:
        self._client = client or OpenAI(api_key=api_key, base_url=base_url)
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

        create_kwargs = {
            "model": self._model_names[request.profile],
            "messages": [
                {"role": event.role.value, "content": event.content}
                for event in request.messages
            ],
            "timeout": request.timeout_seconds,
        }
        if not self._thinking_enabled:
            create_kwargs["extra_body"] = {"thinking": {"type": "disabled"}}
        response = self._client.chat.completions.create(**create_kwargs)
        if cancellation.is_cancelled:
            raise InterruptedError("Model completion was cancelled")
        content = response.choices[0].message.content
        if content is None:
            raise RuntimeError("Model completion did not contain content")
        return LLMResult(content=content)

    def close(self) -> None:
        """Close the request-scoped public SDK client after the application ends."""
        if not self._closed:
            self._client.close()
            self._closed = True
