"""Lifecycle tests for the concrete OpenAI adapter without network calls."""

import unittest

from src.get_me_in.adapters.openai_llm import OpenAILLMAdapter
from src.get_me_in.application.cancellation import CancellationToken
from src.get_me_in.ports.llm import LLMRequest, ModelProfile


class OpenAILLMAdapterTests(unittest.TestCase):
    def test_closed_adapter_rejects_new_completion_without_network(self) -> None:
        adapter = OpenAILLMAdapter(
            api_key="key",
            base_url="https://example.test",
            model_names={ModelProfile.PRO: "pro", ModelProfile.FLASH: "flash"},
        )
        adapter.close()

        with self.assertRaises(RuntimeError):
            adapter.complete(
                LLMRequest(messages=(), profile=ModelProfile.PRO, timeout_seconds=1),
                CancellationToken(),
            )
