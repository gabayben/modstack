from abc import ABC, abstractmethod
from functools import partial
from typing import Optional

from modstack.ai import Embedder, LLM
from modstack.artifacts import Artifact
from modstack.core import SerializableModule
from modstack.query.retrievers import SummaryIndexQuery
from modstack.settings import Settings
from modstack.typing import Effect, Effects

class _SummaryRetriever(SerializableModule[SummaryIndexQuery, list[Artifact]], ABC):
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
    def __init__(self, embedder: Optional[Embedder] = None, **kwargs):
        super().__init__(**kwargs)
        self._embedder = embedder

    def _invoke(self, query: SummaryIndexQuery, **kwargs) -> list[Artifact]:
        pass

    async def _ainvoke(self, query: SummaryIndexQuery, **kwargs) -> list[Artifact]:
        pass

class SummaryLLMRetriever(_SummaryRetriever):
    def __init__(self, llm: LLM = Settings.llm, **kwargs):
        super().__init__(**kwargs)
        self._llm = llm

    def _invoke(self, query: SummaryIndexQuery, **kwargs) -> list[Artifact]:
        pass

    async def _ainvoke(self, query: SummaryIndexQuery, **kwargs) -> list[Artifact]:
        pass