from abc import ABC, abstractmethod
from functools import partial

from modstack.artifacts import Artifact, ArtifactQuery
from modstack.artifacts.messages import MessageChunk
from modstack.indices import ListIndex
from modstack.modules import Module, SerializableModule
from modstack.modules.ai import LLMRequest
from modstack.typing import Effect, Effects

class _ListIndexRetriever(SerializableModule[ArtifactQuery, list[Artifact]], ABC):
    _index: ListIndex

    @property
    def index(self) -> ListIndex:
        return self._index

    def __init__(self, index: ListIndex, **kwargs):
        super().__init__(**kwargs)
        self._index = index

    def forward(self, data: ArtifactQuery, **kwargs) -> Effect[list[Artifact]]:
        return Effects.Provide(
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
    def _invoke(self, data: ArtifactQuery, **kwargs) -> list[Artifact]:
        return self.index.artifact_store.get_many(self.index.struct.artifact_ids, **kwargs)

    async def _ainvoke(self, data: ArtifactQuery, **kwargs) -> list[Artifact]:
        return await self.index.artifact_store.aget_many(self.index.struct.artifact_ids, **kwargs)

# Embedding

class ListIndexEmbeddingRetriever(_ListIndexRetriever):
    def _invoke(self, data: ArtifactQuery, **kwargs) -> list[Artifact]:
        pass

    async def _ainvoke(self, data: ArtifactQuery, **kwargs) -> list[Artifact]:
        pass

# LLM

class ListIndexLLMRetriever(_ListIndexRetriever):
    llm: Module[LLMRequest, list[MessageChunk]]

    def __init__(
        self,
        index: ListIndex,
        llm: Module[LLMRequest, list[MessageChunk]],
        **kwargs
    ):
        super().__init__(index=index, llm=llm, **kwargs)

    def _invoke(self, data: ArtifactQuery, **kwargs) -> list[Artifact]:
        pass

    async def _ainvoke(self, data: ArtifactQuery, **kwargs) -> list[Artifact]:
        pass