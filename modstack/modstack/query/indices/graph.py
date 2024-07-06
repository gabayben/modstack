from dataclasses import dataclass, field
from typing import Optional, Sequence, Unpack, override

from modstack.ai import Embedder
from modstack.artifacts import Artifact
from modstack.config import Settings
from modstack.core import ArtifactTransform, ArtifactTransformLike, Module, coerce_to_module
from modstack.query.indices import IndexData, Indexer
from modstack.query.indices.base import IndexDependencies
from modstack.query.indices.common import CommonIndex
from modstack.query.structs import GraphStruct
from modstack.stores import GraphStore, VectorStore

class GraphIndexDependencies(IndexDependencies, total=False):
    graph_store: GraphStore
    vector_store: VectorStore
    embedder: Embedder
    graph_extractors: Optional[list[ArtifactTransformLike]]
    embed_nodes: bool

@dataclass(kw_only=True)
class GraphIndex(CommonIndex[GraphStruct]):
    graph_store: GraphStore = field(default=Settings.graph_store)
    vector_store: Optional[VectorStore] = field(default=None)
    embedder: Embedder = field(default=Settings.embedder)
    graph_extractors: Optional[list[ArtifactTransformLike]] = field(default=None)
    embed_nodes: bool = field(default=True)

    def __post_init__(self):
        super().__post_init__()
        self.graph_extractors: list[ArtifactTransform] = (
            [coerce_to_module(extractor) for extractor in self.graph_extractors]
            if self.graph_extractors
            else []
        )

    @classmethod
    def indexer(cls, **kwargs: Unpack[GraphIndexDependencies]) -> Module[IndexData[GraphStruct], 'GraphIndex']:
        return Indexer(cls(**kwargs))

    def _build_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> GraphStruct:
        struct = GraphStruct()
        struct.artifact_ids = set([artifact.id for artifact in artifacts])
        self._insert_chunks(list(artifacts), **kwargs)
        return struct

    @override
    async def _abuild_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> GraphStruct:
        struct = GraphStruct()
        struct.artifact_ids = set([artifact.id for artifact in artifacts])
        await self._ainsert_chunks(list(artifacts), **kwargs)
        return struct

    def _insert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        self._insert_chunks(artifacts, **kwargs)
        for artifact in artifacts:
            self.struct.add_artifact(artifact.id)

    def _insert_chunks(self, chunks: list[Artifact], **kwargs) -> list[Artifact]:
        pass

    @override
    async def _ainsert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        await self._ainsert_chunks(artifacts, **kwargs)
        for artifact in artifacts:
            self.struct.add_artifact(artifact.id)

    async def _ainsert_chunks(self, artifacts: list[Artifact], **kwargs) -> list[Artifact]:
        pass

    def _delete(self, artifact_id: str, **kwargs) -> None:
        self.graph_store.delete(ids=[artifact_id], **kwargs)
        self.struct.delete_artifact(artifact_id)

    @override
    async def _adelete(self, artifact_id: str, **kwargs) -> None:
        await self.graph_store.adelete(ids=[artifact_id], **kwargs)
        self.struct.delete_artifact(artifact_id)

    def get_ref_ids(self) -> list[str]:
        return []

    def get_artifact_ids(self) -> list[str]:
        return self.struct.artifact_ids