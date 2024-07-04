from dataclasses import dataclass, field
from typing import Optional, Sequence, override

from modstack.ai import Embedder, LLM
from modstack.artifacts import Artifact
from modstack.core import Module, ModuleLike, coerce_to_module
from modstack.stores import GraphStore, GraphTriplet, RefArtifactInfo
from modstack.query.helpers import LLMTripletExtractor
from modstack.query.indices.simple import SimpleIndex
from modstack.query.structs import KnowledgeGraph
from modstack.config import Settings

@dataclass
class KnowledgeGraphIndex(SimpleIndex[KnowledgeGraph]):
    _graph_store: GraphStore = field(default=Settings.graph_store, kw_only=True)
    _triplet_extractor: Optional[ModuleLike[Artifact, list[GraphTriplet]]] = field(default=None, kw_only=True)
    _embedder: Embedder = field(default=Settings.embedder, kw_only=True)
    _llm: Optional[LLM] = field(default=None, kw_only=True)
    _llm_template: Optional[str] = field(default=None, kw_only=True)
    _max_object_length: Optional[int] = field(default=None, kw_only=True)

    @property
    def graph_store(self) -> GraphStore:
        return self._graph_store

    @property
    def triplet_extractor(self) -> Module[Artifact, list[GraphTriplet]]:
        return self._triplet_extractor

    @property
    def embedder(self) -> Embedder:
        return self._embedder

    def __post_init__(self):
        self._triplet_extractor: Module[Artifact, list[GraphTriplet]] = (
            coerce_to_module(self._triplet_extractor)
            if self._triplet_extractor is not None
            else LLMTripletExtractor(
                llm=self._llm,
                prompt_template=self._llm_template,
                max_object_length=self._max_object_length
            )
        )

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
        raise NotImplementedError('Delete is not yet supported for KnowledgeGraphIndex.')

    def get_refs(self) -> dict[str, RefArtifactInfo]:
        pass

    @override
    async def aget_refs(self) -> dict[str, RefArtifactInfo]:
        pass

    def upsert_triplet_and_chunk(
        self,
        triplet: GraphTriplet,
        chunk: Artifact,
        include_embeddings: bool = False,
        **kwargs
    ) -> None:
        self.upsert_triplet(triplet, **kwargs)
        self.insert_chunk(chunk, [triplet.subject.name, triplet.obj.name])
        if include_embeddings:
            self._embed_triplet(triplet, **kwargs)

    async def aupsert_triplet_and_chunk(
        self,
        triplet: GraphTriplet,
        chunk: Artifact,
        include_embeddings: bool = False,
        **kwargs
    ) -> None:
        await self.aupsert_triplet(triplet, **kwargs)
        await self.ainsert_chunk(chunk, [triplet.subject.name, triplet.obj.name])
        if include_embeddings:
            await self._aembed_triplet(triplet, **kwargs)

    def upsert_triplet(
        self,
        triplet: GraphTriplet,
        include_embeddings: bool = False,
        **kwargs
    ) -> None:
        self.graph_store.upsert_triplet(triplet, **kwargs)
        if include_embeddings:
            self._embed_triplet(triplet, **kwargs)

    async def aupsert_triplet(
        self,
        triplet: GraphTriplet,
        include_embeddings: bool = False,
        **kwargs
    ) -> None:
        await self.graph_store.aupsert_triplet(triplet, **kwargs)
        if include_embeddings:
            await self._aembed_triplet(triplet, **kwargs)

    def insert_chunk(self, chunk: Artifact, keywords: list[str]) -> None:
        self.struct.add_chunk(chunk, keywords)
        self.artifact_store.insert([chunk], allow_update=True)

    async def ainsert_chunk(self, chunk: Artifact, keywords: list[str]) -> None:
        self.struct.add_chunk(chunk, keywords)
        await self.artifact_store.ainsert([chunk], allow_update=True)

    def _embed_triplet(self, triplet: GraphTriplet, **kwargs) -> None:
        artifact = triplet.to_artifact()
        embedding = self.embedder.invoke([artifact])[0].embedding
        self.struct.add_embedding(triplet, embedding)
        self.index_store.upsert_struct(self.struct, **kwargs)

    async def _aembed_triplet(self, triplet: GraphTriplet, **kwargs) -> None:
        artifact = triplet.to_artifact()
        embedding = (await self.embedder.ainvoke([artifact]))[0].embedding
        self.struct.add_embedding(triplet, embedding)
        await self.index_store.aupsert_struct(self.struct, **kwargs)