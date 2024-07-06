from abc import ABC, abstractmethod
from functools import partial
from typing import final

from modstack.artifacts import Artifact
from modstack.core import SerializableModule
from modstack.query.retrievers import GraphIndexQuery
from modstack.typing import Effect, Effects

class GraphSubRetriever(SerializableModule[GraphIndexQuery, list[Artifact]], ABC):
    @final
    def forward(self, query: GraphIndexQuery, **kwargs) -> Effect[list[Artifact]]:
        return Effects.From(
            invoke=partial(self._invoke, query, **kwargs),
            ainvoke=partial(self._ainvoke, query, **kwargs)
        )

    @final
    def _invoke(self, query: GraphIndexQuery, **kwargs) -> list[Artifact]:
        pass

    @abstractmethod
    def _retrieve(self, query: GraphIndexQuery, **kwargs) -> list[Artifact]:
        pass

    @final
    async def _ainvoke(self, query: GraphIndexQuery, **kwargs) -> list[Artifact]:
        pass

    @abstractmethod
    async def _aretrieve(self, query: GraphIndexQuery, **kwargs) -> list[Artifact]:
        pass