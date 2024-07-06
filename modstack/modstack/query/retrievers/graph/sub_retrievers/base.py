from abc import ABC, abstractmethod
from functools import partial
from typing import final

from modstack.artifacts import Artifact
from modstack.core import SerializableModule
from modstack.query.retrievers import VoidIndexQuery
from modstack.typing import Effect, Effects

class GraphSubRetriever(SerializableModule[VoidIndexQuery, list[Artifact]], ABC):
    @final
    def forward(self, query: VoidIndexQuery, **kwargs) -> Effect[list[Artifact]]:
        return Effects.From(
            invoke=partial(self._invoke, query, **kwargs),
            ainvoke=partial(self._ainvoke, query, **kwargs)
        )

    @final
    def _invoke(self, query: VoidIndexQuery, **kwargs) -> list[Artifact]:
        pass

    @abstractmethod
    def _retrieve(self, query: VoidIndexQuery, **kwargs) -> list[Artifact]:
        pass

    @final
    async def _ainvoke(self, query: VoidIndexQuery, **kwargs) -> list[Artifact]:
        pass

    @abstractmethod
    async def _aretrieve(self, query: VoidIndexQuery, **kwargs) -> list[Artifact]:
        pass