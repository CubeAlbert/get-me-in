"""Explicit catalog of immutable agent declarations."""

from collections.abc import Iterable

from src.get_me_in.domain.agents import AgentDescriptor, AgentKey, AgentSpec


class AgentCatalog:
    """Application-owned catalog without module-level registration."""

    def __init__(self, specs: Iterable[AgentSpec]) -> None:
        declared_specs = tuple(specs)
        self._specs = {spec.key: spec for spec in declared_specs}
        if len(self._specs) != len(declared_specs):
            raise ValueError("Agent keys must be unique")

    def get(self, key: AgentKey) -> AgentSpec:
        return self._specs[key]

    def list_descriptors(self) -> tuple[AgentDescriptor, ...]:
        return tuple(
            AgentDescriptor.from_spec(spec)
            for spec in self._specs.values()
        )
