"""Lifecycle tests for the request-scoped OpenAI adapter."""

import threading
from types import SimpleNamespace
import unittest

import httpx
from openai import APITimeoutError

from src.get_me_in.adapters.openai_llm import OpenAILLMAdapter
from src.get_me_in.application.cancellation import CancellationToken
from src.get_me_in.domain.messages import Role
from src.get_me_in.ports.llm import LLMMessage, LLMRequest, ModelProfile
from src.get_me_in.domain.llm_usage import ReportedUsage, UsageUnavailableReason, UnavailableUsage


class OpenAILLMAdapterTests(unittest.TestCase):
    def test_empty_choices_preserve_response_metadata_and_usage_as_missing_content(self) -> None:
        client = _FakeClient()
        client.response = SimpleNamespace(
            model="provider-model",
            choices=(),
            usage=SimpleNamespace(
                prompt_tokens=100,
                completion_tokens=30,
                total_tokens=130,
            ),
        )

        result = _adapter(lambda: client).complete(_request(), CancellationToken())

        self.assertIsNone(result.content)
        self.assertEqual("provider-model", result.response_model)
        self.assertIsInstance(result.usage, ReportedUsage)
        self.assertEqual(130, result.usage.value.total_tokens)

    def test_response_metadata_and_usage_are_normalized_without_requiring_content(self) -> None:
        client = _FakeClient()
        client.response = SimpleNamespace(
            model="provider-model",
            choices=(SimpleNamespace(message=SimpleNamespace(content=None)),),
            usage=SimpleNamespace(
                prompt_tokens=100,
                completion_tokens=30,
                total_tokens=130,
                prompt_tokens_details=SimpleNamespace(cached_tokens=20),
                completion_tokens_details=SimpleNamespace(reasoning_tokens=10),
            ),
        )

        result = _adapter(lambda: client).complete(_request(), CancellationToken())

        self.assertIsNone(result.content)
        self.assertEqual("provider-model", result.response_model)
        self.assertIsInstance(result.usage, ReportedUsage)
        self.assertEqual(20, result.usage.value.cached_input_tokens)

    def test_missing_core_usage_is_typed_unknown(self) -> None:
        client = _FakeClient()
        client.response = SimpleNamespace(
            model="provider-model",
            choices=(SimpleNamespace(message=SimpleNamespace(content='{"content": "ok"}')),),
            usage=SimpleNamespace(prompt_tokens=100),
        )

        result = _adapter(lambda: client).complete(_request(), CancellationToken())

        self.assertIsInstance(result.usage, UnavailableUsage)
        self.assertEqual(UsageUnavailableReason.NOT_REPORTED, result.usage.reason)

    def test_inconsistent_provider_total_is_malformed_usage(self) -> None:
        client = _FakeClient()
        client.response = SimpleNamespace(
            model="provider-model",
            choices=(SimpleNamespace(message=SimpleNamespace(content='{"content": "ok"}')),),
            usage=SimpleNamespace(prompt_tokens=100, completion_tokens=30, total_tokens=129),
        )

        result = _adapter(lambda: client).complete(_request(), CancellationToken())

        self.assertIsInstance(result.usage, UnavailableUsage)
        self.assertEqual(UsageUnavailableReason.MALFORMED, result.usage.reason)

    def test_api_timeout_error_is_mapped_to_builtin_timeout(self) -> None:
        client = _FakeClient()
        client.chat.completions.error = APITimeoutError(
            httpx.Request("POST", "https://example.test")
        )

        with self.assertRaises(TimeoutError):
            _adapter(lambda: client).complete(_request(), CancellationToken())

    def test_closed_adapter_rejects_new_completion_without_creating_client(self) -> None:
        created: list[object] = []
        adapter = _adapter(lambda: created.append(object()))
        adapter.close()

        with self.assertRaises(RuntimeError):
            adapter.complete(_request(), CancellationToken())

        self.assertEqual([], created)

    def test_request_client_receives_settings_and_is_closed(self) -> None:
        client = _FakeClient()
        adapter = _adapter(lambda: client, thinking_enabled=False)

        adapter.complete(_request(), CancellationToken())

        self.assertEqual({"thinking": {"type": "disabled"}}, client.create_kwargs["extra_body"])
        self.assertEqual(
            {"type": "json_object"},
            client.create_kwargs["response_format"],
        )
        self.assertEqual(1, client.close_calls)
        self.assertEqual([{"role": "user", "content": "hello"}], client.create_kwargs["messages"])

    def test_temperature_is_forwarded_only_when_explicit(self) -> None:
        configured_client = _FakeClient()
        unset_client = _FakeClient()

        _adapter(lambda: configured_client).complete(_request(temperature=0.2), CancellationToken())
        _adapter(lambda: unset_client).complete(_request(), CancellationToken())

        self.assertEqual(0.2, configured_client.create_kwargs["temperature"])
        self.assertNotIn("temperature", unset_client.create_kwargs)

    def test_invalid_temperature_is_rejected_without_creating_client(self) -> None:
        created: list[object] = []
        adapter = _adapter(lambda: created.append(object()))

        with self.assertRaises(ValueError):
            adapter.complete(_request(temperature=float("nan")), CancellationToken())

        self.assertEqual([], created)

    def test_cancellation_closes_the_active_request_and_adapter_remains_reusable(self) -> None:
        blocking = _BlockingClient()
        succeeding = _FakeClient()
        clients = iter((blocking, succeeding))
        adapter = _adapter(lambda: next(clients))
        token = CancellationToken()
        errors: list[BaseException] = []

        worker = threading.Thread(
            target=lambda: _capture_error(errors, lambda: adapter.complete(_request(), token))
        )
        worker.start()
        self.assertTrue(blocking.started.wait(timeout=1))
        token.cancel()
        worker.join(timeout=1)

        self.assertFalse(worker.is_alive())
        self.assertGreaterEqual(blocking.close_calls, 1)
        token.reset()
        self.assertEqual('{"content": "ok"}', adapter.complete(_request(), token).content)


def _adapter(factory, *, thinking_enabled: bool = True) -> OpenAILLMAdapter:
    return OpenAILLMAdapter(
        api_key="key",
        base_url="https://example.test",
        model_names={ModelProfile.PRO: "pro", ModelProfile.FLASH: "flash"},
        thinking_enabled=thinking_enabled,
        client_factory=factory,
    )


def _request(*, temperature: float | None = None) -> LLMRequest:
    return LLMRequest(
        messages=(LLMMessage(Role.USER, "hello"),),
        profile=ModelProfile.PRO,
        timeout_seconds=1,
        temperature=temperature,
    )


def _capture_error(errors: list[BaseException], callback) -> None:
    try:
        callback()
    except BaseException as error:
        errors.append(error)


class _FakeClient:
    def __init__(self) -> None:
        self.chat = _FakeChat(self)
        self.create_kwargs: dict = {}
        self.close_calls = 0
        self.response = None

    def close(self) -> None:
        self.close_calls += 1


class _BlockingClient(_FakeClient):
    def __init__(self) -> None:
        super().__init__()
        self.started = threading.Event()
        self.closed = threading.Event()

    def close(self) -> None:
        super().close()
        self.closed.set()


class _FakeChat:
    def __init__(self, client: _FakeClient) -> None:
        self.completions = _FakeCompletions(client)


class _FakeCompletions:
    def __init__(self, client: _FakeClient) -> None:
        self._client = client
        self.error = None

    def create(self, **kwargs):
        self._client.create_kwargs = kwargs
        if self.error is not None:
            raise self.error
        if isinstance(self._client, _BlockingClient):
            self._client.started.set()
            self._client.closed.wait(timeout=2)
            raise InterruptedError("closed")
        return self._client.response or _FakeResponse()


class _FakeResponse:
    class _Choice:
        class _Message:
            content = '{"content": "ok"}'

        message = _Message()

    choices = (_Choice(),)
