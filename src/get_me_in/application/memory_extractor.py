"""Extract typed memory records from an immutable copied conversation source."""

import json

from src.get_me_in.domain.memories import MemoryBuildSource, MemoryCategory, MemoryRecord
from src.get_me_in.ports.llm import LLMMessage, LLMPort, LLMRequest, ModelProfile, CancellationSignal
from src.get_me_in.domain.messages import Role


class MemoryExtractor:
    def __init__(self, llm: LLMPort, prompt: str, clock: object, id_generator: object, timeout_seconds: float) -> None:
        self._llm, self._prompt, self._clock, self._ids, self._timeout = llm, prompt, clock, id_generator, timeout_seconds

    def extract(self, source: MemoryBuildSource, cancellation: CancellationSignal) -> tuple[MemoryRecord, ...]:
        text = "\n".join(record.content for record in source.records if hasattr(record, "content"))
        result = self._llm.complete(LLMRequest((LLMMessage(role=Role.SYSTEM, content=self._prompt), LLMMessage(role=Role.USER, content=text)), ModelProfile.FLASH, self._timeout), cancellation)
        values = json.loads(result.content)
        records = []
        for item in values:
            category, content = MemoryCategory(item["category"]), item["content"].strip()
            if not content: raise ValueError("empty memory content")
            records.append(MemoryRecord(1, self._ids.new_id(), source.agent_key, category, content, self._clock.now()))
        return tuple(records)

    def close(self) -> None:
        self._llm.close()
