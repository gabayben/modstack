from abc import ABC, abstractmethod
from functools import partial
from typing import Optional

from modstack.artifacts import Artifact, ArtifactQuery
from modstack.querying.indices import ListIndex
from modstack.querying.indices.structs import ListStruct
from modstack.modules import Module, SerializableModule
from modstack.data.stores import ArtifactStore
from modstack.typing import Effect, Effects

class _ListIndexRetriever(SerializableModule[ArtifactQuery, list[Artifact]], ABC):
    @property
    def index(self) -> ListIndex:
        return self._index

    @property
    def struct(self) -> ListStruct:
        return self.index.struct

    @property
    def artifact_store(self) -> ArtifactStore:
        return self.index.artifact_store

    def __init__(self, index: ListIndex, **kwargs):
        super().__init__(**kwargs)
        self._index = index

    def forward(self, data: ArtifactQuery, **kwargs) -> Effect[list[Artifact]]:
        return Effects.From(
            invoke=partial(self._invoke, data, **kwargs),
            ainvoke=partial(self._ainvoke, data, **kwargs)
        )

    @abstractmethod
    def _invoke(self, data: ArtifactQuery, **kwargs) -> list[Artifact]:
        pass

    @abstractmethod
    async def _ainvoke(self, data: ArtifactQuery, **kwargs) -> list[Artifact]:
        pass

# Simple

class ListIndexSimpleRetriever(_ListIndexRetriever):
    def _invoke(self, _: ArtifactQuery, **kwargs) -> list[Artifact]:
        return self.artifact_store.get_many(self.struct.artifact_ids, **kwargs)

    async def _ainvoke(self, _: ArtifactQuery, **kwargs) -> list[Artifact]:
        return await self.artifact_store.aget_many(self.struct.artifact_ids, **kwargs)

# Embedding

class ListIndexEmbeddingRetriever(_ListIndexRetriever):
    def __init__(
        self,
        index: ListIndex,
        embed_model: Module[list[Artifact], list[Artifact]],
        ranker: Module[list[Artifact], list[Artifact]],
        top_k: Optional[int] = 1,
        **kwargs
    ):
        super().__init__(index, **kwargs)
        self._embed_model = embed_model
        self._ranker = ranker
        self._top_k = top_k

    def _invoke(self, data: ArtifactQuery, **kwargs) -> list[Artifact]:
        artifacts = self.artifact_store.get_many(self.struct.artifact_ids)
        query, artifacts = self._get_embeddings(data.value, artifacts, **kwargs)
        return self._ranker.invoke(artifacts, top_k=self._top_k, **kwargs)

    def _get_embeddings(
        self,
        query: Artifact,
        artifacts: list[Artifact],
        **kwargs
    ) -> tuple[Artifact, list[Artifact]]:
        if query.embedding is None:
            query = self._embed_model.invoke([query], **kwargs)[0]
        artifacts = self._embed_model.invoke(artifacts, **kwargs)
        return query, artifacts

    async def _ainvoke(self, data: ArtifactQuery, **kwargs) -> list[Artifact]:
        artifacts = await self.artifact_store.aget_many(self.struct.artifact_ids)
        query, artifacts = await self._aget_embeddings(data.value, artifacts, **kwargs)
        return await self._ranker.ainvoke(artifacts, top_k=self._top_k, **kwargs)

    async def _aget_embeddings(
        self,
        query: Artifact,
        artifacts: list[Artifact],
        **kwargs
    ) -> tuple[Artifact, list[Artifact]]:
        if query.embedding is None:
            query = (await self._embed_model.ainvoke([query], **kwargs))[0]
        artifacts = await self._embed_model.ainvoke(artifacts, **kwargs)
        return query, artifacts