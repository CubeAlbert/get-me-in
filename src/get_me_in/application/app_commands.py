"""Application-level commands that must never enter AgentRuntime."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ApplicationCommand:
    pass


@dataclass(frozen=True)
class RestoreSession(ApplicationCommand):
    session_id: str


@dataclass(frozen=True)
class RewindSession(ApplicationCommand):
    turn_id: str


@dataclass(frozen=True)
class ExitSubAgent(ApplicationCommand):
    pass


@dataclass(frozen=True)
class DumpSession(ApplicationCommand):
    pass


@dataclass(frozen=True)
class ReloadKnowledge(ApplicationCommand):
    target: str | None = None


@dataclass(frozen=True)
class BuildMemory(ApplicationCommand):
    pass
