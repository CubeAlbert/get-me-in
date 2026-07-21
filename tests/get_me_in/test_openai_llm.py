"""Lifecycle tests for the concrete OpenAI adapter without network calls."""

import unittest
from datetime import datetime, timezone

from src.get_me_in.adapters.openai_llm import OpenAILLMAdapter
from src.get_me_in.application.cancellation import CancellationToken
from src.get_me_in.domain.messages import ConversationEvent, EventKind, Role
from src.get_me_in.ports.llm import LLMRequest, ModelProfile


class OpenAILLMAdapterTests(unittest.TestCase):
    def test_closed_adapter_rejects_new_completion_without_network(self) -> None:
        adapter = OpenAILLMAdapter(
            api_key="key",
            base_url="https://example.test",
            model_names={ModelProfile.PRO: "pro", ModelProfile.FLASH: "flash"},
            thinking_enabled=True,
        )
        adapter.close()

        with self.assertRaises(RuntimeError):
            adapter.complete(
                LLMRequest(messages=(), profile=ModelProfile.PRO, timeout_seconds=1),
                CancellationToken(),
            )

    def test_disabled_thinking_is_forwarded_to_the_provider(self) -> None:
        client = _FakeClient()
        adapter = _adapter(client=client, thinking_enabled=False)

        adapter.complete(_request(), CancellationToken())

        self.assertEqual(
            {"thinking": {"type": "disabled"}},
            client.create_kwargs["extra_body"],
        )

    def test_enabled_thinking_uses_the_provider_default(self) -> None:
        client = _FakeClient()
        adapter = _adapter(client=client, thinking_enabled=True)

        adapter.complete(_request(), CancellationToken())

        self.assertNotIn("extra_body", client.create_kwargs)


def _adapter(*, client: "_FakeClient", thinking_enabled: bool) -> OpenAILLMAdapter:
    return OpenAILLMAdapter(
        api_key="key",
        base_url="https://example.test",
        model_names={ModelProfile.PRO: "pro", ModelProfile.FLASH: "flash"},
        thinking_enabled=thinking_enabled,
        client=client,
    )


def _request() -> LLMRequest:
    return LLMRequest(
        messages=(
            ConversationEvent(
                event_id="event",
                role=Role.USER,
                kind=EventKind.MESSAGE,
                content="hello",
                timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
            ),
        ),
        profile=ModelProfile.PRO,
        timeout_seconds=1,
    )


class _FakeClient:
    def __init__(self) -> None:
        self.chat = _FakeChat(self)
        self.create_kwargs: dict = {}

    def close(self) -> None:
        pass


class _FakeChat:
    def __init__(self, client: _FakeClient) -> None:
        self.completions = _FakeCompletions(client)


class _FakeCompletions:
    def __init__(self, client: _FakeClient) -> None:
        self._client = client

    def create(self, **kwargs):
        self._client.create_kwargs = kwargs
        return _FakeResponse()


class _FakeResponse:
    class _Choice:
        class _Message:
            content = '{"content": "ok"}'

        message = _Message()

    choices = (_Choice(),)
