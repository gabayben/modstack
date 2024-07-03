from dataclasses import field
from typing import Sequence, override

from modstack.artifacts import Artifact
from modstack.data.stores import GraphStore, RefArtifactInfo
from modstack.query.indices.artifact_store import ArtifactStoreIndex
from modstack.query.structs import KnowledgeGraph
from modstack.settings import Settings

class KnowledgeGraphIndex(ArtifactStoreIndex[KnowledgeGraph]):
    _graph_store: GraphStore = field(default=Settings.graph_store, kw_only=True)

    @property
    def graph_store(self) -> GraphStore:
        return self._graph_store

    def _build_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> KnowledgeGraph:
        pass

    @override
    async def _abuild_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> KnowledgeGraph:
        pass

    def _insert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        pass

    @override
    async def _ainsert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        pass

    def _delete(self, artifact_id: str, **kwargs) -> None:
        raise NotImplementedError(f'Delete is not supported for KnowledgeGraphIndex yet.')

    def get_refs(self) -> dict[str, RefArtifactInfo]:
        pass

    @override
    async def aget_refs(self) -> dict[str, RefArtifactInfo]:
        pass