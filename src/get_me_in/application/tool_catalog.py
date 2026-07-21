"""Application-owned catalog of explicitly assembled tool definitions."""

from collections.abc import Iterable

from src.get_me_in.domain.agents import Capability
from src.get_me_in.domain.tools import ToolDefinition


class ToolCatalog:
    """Provides capability-filtered tools without a global registry."""

    def __init__(self, definitions: Iterable[ToolDefinition]) -> None:
        declared = tuple(definitions)
        self._definitions = {definition.name: definition for definition in declared}
        if len(self._definitions) != len(declared):
            raise ValueError("Tool names must be unique")

    def get(self, name: str) -> ToolDefinition:
        return self._definitions[name]

    def list_for_capabilities(
        self,
        capabilities: frozenset[Capability],
    ) -> tuple[ToolDefinition, ...]:
        return tuple(
            definition
            for definition in self._definitions.values()
            if definition.policy.required_capabilities <= capabilities
        )

    def export_descriptors(self) -> tuple[dict[str, object], ...]:
        """Expose the effective tool directory for diagnostics and prompts."""
        return tuple(
            {
                "name": definition.name,
                "description": definition.description,
                "required": tuple(sorted(definition.schema.required)),
                "properties": tuple(sorted(definition.schema.properties)),
            }
            for definition in self._definitions.values()
        )
