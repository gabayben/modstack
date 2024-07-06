from abc import ABC, abstractmethod
from functools import partial
from typing import Optional, final

from modstack.ai import Embedder, LLM
from modstack.ai.utils import aembed_query, embed_query
from modstack.artifacts import Artifact
from modstack.core import SerializableModule
from modstack.stores import VectorStoreQuery, VectorStoreQueryResult
from modstack.query.retrievers import SummaryIndexQuery
from modstack.config import Settings
from modstack.typing import Effect, Effects

class _SummaryRetriever(SerializableModule[SummaryIndexQuery, list[Artifact]], ABC):
    @final
    def forward(self, query: SummaryIndexQuery, **kwargs) -> Effect[list[Artifact]]:
        return Effects.From(
            invoke=partial(self._invoke, query, **kwargs),
            ainvoke=partial(self._ainvoke, query, **kwargs)
        )

    @abstractmethod
    def _invoke(self, query: SummaryIndexQuery, **kwargs) -> list[Artifact]:
        pass

    @abstractmethod
    async def _ainvoke(self, query: SummaryIndexQuery, **kwargs) -> list[Artifact]:
        pass

class SummaryEmbeddingRetriever(_SummaryRetriever):
    def __init__(
        self,
        embedder: Optional[Embedder] = None,
        top_k: int = 1,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._embedder = embedder
        self._top_k = top_k

    def _invoke(self, query: SummaryIndexQuery, **kwargs) -> list[Artifact]:
        index = query.index
        embedder = self._embedder or index.embedder
        embedded_value = embed_query(embedder, query.value, **kwargs)

        query_result = index.vector_store.retrieve(query_embedding=embedded_value.embedding, similarity_top_k=self._top_k)
        top_k_summary_ids = self._extract_top_k_summary_ids(query_result)

        results: list[Artifact] = []
        for summary_id in top_k_summary_ids:
            chunk_ids = index.struct.chunk_ids
            chunks = index.artifact_store.get_many(chunk_ids)
            results.extend(chunks)
        return results

    async def _ainvoke(self, query: SummaryIndexQuery, **kwargs) -> list[Artifact]:
        index = query.index
        embedder = self._embedder or index.embedder
        embedded_value = await aembed_query(embedder, query.value, **kwargs)

        query_result = await index.vector_store.aretrieve(query_embedding=embedded_value.embedding, similarity_top_k=self._top_k)
        top_k_summary_ids = self._extract_top_k_summary_ids(query_result)

        results: list[Artifact] = []
        for summary_id in top_k_summary_ids:
            chunk_ids = index.struct.chunk_ids
            chunks = await index.artifact_store.aget_many(chunk_ids)
            results.extend(chunks)
        return results

    def _extract_top_k_summary_ids(self, query_result: VectorStoreQueryResult) -> list[str]:
        top_k_summary_ids: list[str]
        if query_result.ids is not None:
            top_k_summary_ids = query_result.ids
        elif query_result.artifacts is not None:
            top_k_summary_ids = [artifact.id for artifact in query_result.artifacts]
        else:
            raise ValueError('VectorStore.retrieve(...) must return ids or artifacts.')
        return top_k_summary_ids

class SummaryLLMRetriever(_SummaryRetriever):
    def __init__(self, llm: LLM = Settings.llm, **kwargs):
        super().__init__(**kwargs)
        self._llm = llm

    def _invoke(self, query: SummaryIndexQuery, **kwargs) -> list[Artifact]:
        pass

    async def _ainvoke(self, query: SummaryIndexQuery, **kwargs) -> list[Artifact]:
        pass