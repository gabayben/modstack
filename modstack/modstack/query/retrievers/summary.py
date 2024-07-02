from abc import ABC, abstractmethod
from functools import partial

from modstack.modules import Embedder, LLM
from modstack.artifacts import Artifact
from modstack.core import SerializableModule
from modstack.query.indices import SummaryIndex
from modstack.typing import Effect, Effects

class _SummaryRetriever(SerializableModule[Artifact, list[Artifact]], ABC):
    @property
    def index(self) -> SummaryIndex:
        return self._index

    def __init__(self, index: SummaryIndex, **kwargs):
        super().__init__(**kwargs)
        self._index = index

    def forward(self, query: Artifact, **kwargs) -> Effect[list[Artifact]]:
        return Effects.From(
            invoke=partial(self._invoke, query, **kwargs),
            ainvoke=partial(self._ainvoke, query, **kwargs)
        )

    @abstractmethod
    def _invoke(self, query: Artifact, **kwargs) -> list[Artifact]:
        pass

    @abstractmethod
    async def _ainvoke(self, query: Artifact, **kwargs) -> list[Artifact]:
        pass

class SummaryEmbeddingRetriever(_SummaryRetriever):
    def __init__(
        self,
        index: SummaryIndex,
        embed_model: Embedder,
        **kwargs
    ):
        super().__init__(index, **kwargs)
        self._embed_model = embed_model

    def _invoke(self, query: Artifact, **kwargs) -> list[Artifact]:
        pass

    async def _ainvoke(self, query: Artifact, **kwargs) -> list[Artifact]:
        pass

class SummaryLLMRetriever(_SummaryRetriever):
    def __init__(
        self,
        index: SummaryIndex,
        llm: LLM,
        **kwargs
    ):
        super().__init__(index, **kwargs)
        self._llm = llm

    def _invoke(self, query: Artifact, **kwargs) -> list[Artifact]:
        pass

    async def _ainvoke(self, query: Artifact, **kwargs) -> list[Artifact]:
        pass