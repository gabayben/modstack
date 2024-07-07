from dataclasses import dataclass, field
from typing import Optional, Sequence, Unpack, override

from modstack.ai import Embedder, LLM
from modstack.artifacts import Artifact
from modstack.config import Settings
from modstack.core import ArtifactTransform, ArtifactTransformLike, Module, coerce_to_module
from modstack.core.utils import run_transformations
from modstack.query.helpers import ImplicitGraphExtractor, SimpleLLMGraphExtractor
from modstack.query.indices import IndexData, Indexer
from modstack.query.indices.base import IndexDependencies
from modstack.query.indices.common import CommonIndex
from modstack.query.structs import GraphStruct
from modstack.stores import GraphNode, GraphRelation, GraphStore, VectorStore
from modstack.utils.constants import GRAPH_NODES_KEY, GRAPH_RELATIONS_KEY

class GraphIndexDependencies(IndexDependencies, total=False):
    graph_store: GraphStore
    vector_store: VectorStore
    embedder: Embedder
    llm: LLM
    graph_extractors: Optional[list[ArtifactTransformLike]]
    embed_nodes: bool

@dataclass(kw_only=True)
class GraphIndex(CommonIndex[GraphStruct]):
    graph_store: GraphStore = field(default=Settings.graph_store)
    vector_store: Optional[VectorStore] = field(default=None)
    embedder: Embedder = field(default=Settings.embedder)
    llm: LLM = field(default=Settings.llm)
    graph_extractors: Optional[list[ArtifactTransformLike]] = field(default=None)
    embed_nodes: bool = field(default=True)

    def __post_init__(self):
        super().__post_init__()
        self.graph_extractors: list[ArtifactTransform] = (
            [coerce_to_module(extractor) for extractor in self.graph_extractors]
            if self.graph_extractors
            else [
                SimpleLLMGraphExtractor(llm=self.llm),
                ImplicitGraphExtractor()
            ]
        )

    @classmethod
    def indexer(cls, **kwargs: Unpack[GraphIndexDependencies]) -> Module[IndexData[GraphStruct], 'GraphIndex']:
        return Indexer(cls(**kwargs))

    def _build_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> GraphStruct:
        chunks = self._insert_chunks(list(artifacts), **kwargs)
        struct = GraphStruct()
        struct.artifact_ids = set([chunk.id for chunk in chunks])
        return struct

    @override
    async def _abuild_from_artifacts(self, artifacts: Sequence[Artifact], **kwargs) -> GraphStruct:
        chunks = await self._ainsert_chunks(list(artifacts), **kwargs)
        struct = GraphStruct()
        struct.artifact_ids = set([chunk.id for chunk in chunks])
        return struct

    def _insert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        chunks = self._insert_chunks(artifacts, **kwargs)
        for chunk in chunks:
            self.struct.add_artifact(chunk.id)

    def _insert_chunks(self, chunks: list[Artifact], **kwargs) -> list[Artifact]:
        if len(chunks) == 0:
            return chunks

        chunks = run_transformations(
            chunks,
            self.graph_extractors,
            cache=self.cache,
            cache_collection=self.cache_collection
        )

        assert all(
            chunk.metadata.get(GRAPH_NODES_KEY) is not None
            or chunk.metadata.get(GRAPH_RELATIONS_KEY) is not None
            for chunk in chunks
        )

        nodes_to_insert: list[GraphNode] = []
        relations_to_insert: list[GraphRelation] = []
        for chunk in chunks:
            nodes: list[GraphNode] = chunk.metadata.pop(GRAPH_NODES_KEY)
            relations: list[GraphRelation] = chunk.metadata.pop(GRAPH_RELATIONS_KEY)

    @override
    async def _ainsert_many(self, artifacts: list[Artifact], **kwargs) -> None:
        chunks = await self._ainsert_chunks(artifacts, **kwargs)
        for chunk in chunks:
            self.struct.add_artifact(chunk.id)

    async def _ainsert_chunks(self, artifacts: list[Artifact], **kwargs) -> list[Artifact]:
        pass

    def _get_chunks_with_embeddings(self, nodes: list[GraphNode]) -> list[Artifact]:
        chunks_to_insert: list[Artifact] = []
        for node in nodes:
            if node.embedding is not None:
                chunks_to_insert.append(node.to_artifact())
        return chunks_to_insert

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