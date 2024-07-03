from abc import ABC, abstractmethod
from functools import partial
from typing import final

from modstack.artifacts import Artifact
from modstack.core import SerializableModule
from modstack.query.retrievers import KnowledgeGraphQuery
from modstack.typing import Effect, Effects

class KnowledgeGraphBaseRetriever(SerializableModule[KnowledgeGraphQuery, list[Artifact]], ABC):
    @final
    def forward(self, query: KnowledgeGraphQuery, **kwargs) -> Effect[list[Artifact]]:
        return Effects.From(
            invoke=partial(self._invoke, query, **kwargs),
            ainvoke=partial(self._ainvoke, query, **kwargs)
        )

    @abstractmethod
    def _invoke(self, query: KnowledgeGraphQuery, **kwargs) -> list[Artifact]:
        pass

    @abstractmethod
    async def _ainvoke(self, query: KnowledgeGraphQuery, **kwargs) -> list[Artifact]:
        pass