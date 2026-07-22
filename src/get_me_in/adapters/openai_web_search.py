"""Request-scoped OpenAI native-function implementation of WebSearchPort."""

from collections.abc import Callable

from openai import OpenAI

from src.get_me_in.ports.llm import CancellationSignal


_WEB_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web for information",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query",
                }
            },
            "required": ["query"],
        },
    },
}

_WEB_SEARCH_SYSTEM = (
    "You are a web search tool. Your only job is to perform a single "
    "web search for the given query and return the results. "
    "Do not engage in conversation, ask follow-up questions, "
    "or mention that you are an AI model. "
    "Just return the search results directly."
)

_MAX_TOKENS = 4096
_DSML_TOOL_CALL_MARKER = "<｜｜DSML｜｜tool_calls>"


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
                max_tokens=_MAX_TOKENS,
                messages=[
                    {"role": "system", "content": _WEB_SEARCH_SYSTEM},
                    {"role": "user", "content": f"Perform a web search for the query: {query}"},
                ],
                tools=[_WEB_SEARCH_TOOL],
                tool_choice={"type": "function", "function": {"name": "web_search"}},
                extra_body={"thinking": {"type": "disabled"}},
            )
            if cancellation.is_cancelled:
                raise InterruptedError("Web search was cancelled")
            message = response.choices[0].message
            if not message.tool_calls:
                content = message.content or ""
                if _DSML_TOOL_CALL_MARKER in content:
                    raise RuntimeError("DeepSeek returned an unexecuted web_search tool call")
                return content
            call = message.tool_calls[0]
            response = client.chat.completions.create(
                model=self._model,
                max_tokens=_MAX_TOKENS,
                messages=[
                    {"role": "system", "content": _WEB_SEARCH_SYSTEM},
                    {"role": "user", "content": f"Perform a web search for the query: {query}"},
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
