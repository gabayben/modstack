from dataclasses import dataclass, field
from typing import Optional, Sequence, Unpack, override

from modstack.ai import Embedder
from modstack.artifacts import Artifact
from modstack.config import Settings
from modstack.core import ArtifactTransform, ArtifactTransformLike, Module, coerce_to_module
from modstack.query.indices import IndexData, Indexer
from modstack.query.indices.base import IndexDependencies
from modstack.query.indices.common import CommonIndex
from modstack.query.structs import VoidStruct
from modstack.stores import GraphStore, RefArtifactInfo, VectorStore

class GraphIndexDependencies(IndexDependencies, total=False):
    graph_store: GraphStore
    vector_store: VectorStore
    embedder: Embedder
    graph_extractors: Optional[list[ArtifactTransformLike]]
    embed_nodes: bool

@dataclass(kw_only=True)
class GraphIndex(CommonIndex[VoidStruct]):
    graph_store: GraphStore = field(default=Settings.graph_store)
    vector_store: VectorStore = field(default=Settings.vector_store)
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
    def indexer(cls, **kwargs: Unpack[GraphIndexDependencies]) -> Module[IndexData[VoidStruct], 'GraphIndex']:
        return Indexer(cls(**kwargs))

    def _build_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> VoidStruct:
        pass

    @override
    async def _abuild_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> VoidStruct:
        pass

    def _insert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        pass

    @override
    async def _ainsert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        pass

    def _delete(self, artifact_id: str, **kwargs) -> None:
        pass

    @override
    async def _adelete(self, artifact_id: str, **kwargs) -> None:
        pass

    def get_refs(self) -> dict[str, RefArtifactInfo]:
        pass

    @override
    async def aget_refs(self) -> dict[str, RefArtifactInfo]:
        pass