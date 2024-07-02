from abc import ABC, abstractmethod
from functools import partial
from typing import Optional

from modstack.ai import Embedder
from modstack.artifacts import Artifact
from modstack.core import Module, SerializableModule
from modstack.query.retrievers import ListIndexQuery
from modstack.typing import Effect, Effects

class _ListIndexRetriever(SerializableModule[ListIndexQuery, list[Artifact]], ABC):
    def forward(self, query: ListIndexQuery, **kwargs) -> Effect[list[Artifact]]:
        return Effects.From(
            invoke=partial(self._invoke, query, **kwargs),
            ainvoke=partial(self._ainvoke, query, **kwargs)
        )

    @abstractmethod
    def _invoke(self, query: ListIndexQuery, **kwargs) -> list[Artifact]:
        pass

    @abstractmethod
    async def _ainvoke(self, query: ListIndexQuery, **kwargs) -> list[Artifact]:
        pass

class ListIndexSimpleRetriever(_ListIndexRetriever):
    def _invoke(self, query: ListIndexQuery, **kwargs) -> list[Artifact]:
        return query.index.artifact_store.get_many(query.index.struct.artifact_ids, **kwargs)

    async def _ainvoke(self, query: ListIndexQuery, **kwargs) -> list[Artifact]:
        return await query.index.artifact_store.aget_many(query.index.struct.artifact_ids, **kwargs)

class ListIndexEmbeddingRetriever(_ListIndexRetriever):
    def __init__(
        self,
        embedder: Embedder,
        ranker: Module[list[Artifact], list[Artifact]],
        top_k: Optional[int] = 1,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._embedder = embedder
        self._ranker = ranker
        self._top_k = top_k

    def _invoke(self, query: ListIndexQuery, **kwargs) -> list[Artifact]:
        artifacts = query.index.artifact_store.get_many(query.index.struct.artifact_ids)
        query_value, artifacts = self._get_embeddings(query.value, artifacts, **kwargs)
        return self._ranker.invoke(artifacts, top_k=self._top_k, **kwargs)

    def _get_embeddings(
        self,
        query: Artifact,
        artifacts: list[Artifact],
        **kwargs
    ) -> tuple[Artifact, list[Artifact]]:
        if query.embedding is None:
            query = self._embedder.invoke([query], **kwargs)[0]
        artifacts = self._embedder.invoke(artifacts, **kwargs)
        return query, artifacts

    async def _ainvoke(self, query: ListIndexQuery, **kwargs) -> list[Artifact]:
        artifacts = await query.index.artifact_store.aget_many(query.index.struct.artifact_ids)
        query_value, artifacts = await self._aget_embeddings(query.value, artifacts, **kwargs)
        return await self._ranker.ainvoke(artifacts, top_k=self._top_k, **kwargs)

    async def _aget_embeddings(
        self,
        query: Artifact,
        artifacts: list[Artifact],
        **kwargs
    ) -> tuple[Artifact, list[Artifact]]:
        if query.embedding is None:
            query = (await self._embedder.ainvoke([query], **kwargs))[0]
        artifacts = await self._embedder.ainvoke(artifacts, **kwargs)
        return query, artifacts