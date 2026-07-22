"""Request-scoped OpenAI native-function implementation of WebSearchPort."""

from collections.abc import Callable

from openai import OpenAI

from src.get_me_in.ports.llm import CancellationSignal


class OpenAIWebSearchAdapter:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        client_factory: Callable[[], OpenAI] | None = None,
    ) -> None:
        self._client_factory = client_factory or (
            lambda: OpenAI(api_key=api_key, base_url=base_url)
        )
        self._model = model
        self._closed = False

    def search(self, query: str, cancellation: CancellationSignal) -> str:
        if self._closed:
            raise RuntimeError("OpenAIWebSearchAdapter is closed")
        if cancellation.is_cancelled:
            raise InterruptedError("Web search was cancelled")
        client = self._client_factory()
        registration = cancellation.register(client.close)
        try:
            response = client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": "Search the web once and return a concise sourced answer."},
                    {"role": "user", "content": query},
                ],
                tools=[{"type": "function", "function": {"name": "web_search", "description": "Search the web", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}}],
                tool_choice={"type": "function", "function": {"name": "web_search"}},
                extra_body={"thinking": {"type": "disabled"}},
            )
            if cancellation.is_cancelled:
                raise InterruptedError("Web search was cancelled")
            message = response.choices[0].message
            if not message.tool_calls:
                return message.content or ""
            call = message.tool_calls[0]
            response = client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": "Search the web once and return a concise sourced answer."},
                    {"role": "user", "content": query},
                    {"role": "assistant", "content": message.content or "", "tool_calls": [{"id": call.id, "type": "function", "function": {"name": call.function.name, "arguments": call.function.arguments}}]},
                    {"role": "tool", "tool_call_id": call.id, "content": "Provide the result"},
                ],
                extra_body={"thinking": {"type": "disabled"}},
            )
            if cancellation.is_cancelled:
                raise InterruptedError("Web search was cancelled")
            return response.choices[0].message.content or ""
        finally:
            registration.close()
            client.close()

    def close(self) -> None:
        self._closed = True
