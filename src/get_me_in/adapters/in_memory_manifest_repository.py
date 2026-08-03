"""Process-local manifest storage for an ephemeral knowledge index."""

from src.get_me_in.domain.knowledge import IndexManifest


class InMemoryManifestRepository:
    """Keep index commit state in memory for the lifetime of one application."""

    def __init__(self) -> None:
        self._manifest = IndexManifest(1)

    def load(self) -> IndexManifest:
        return self._manifest

    def save(self, manifest: IndexManifest) -> None:
        if manifest.schema_version != 1:
            raise ValueError("unsupported knowledge manifest schema")
        self._manifest = manifest

    def close(self) -> None:
        pass
