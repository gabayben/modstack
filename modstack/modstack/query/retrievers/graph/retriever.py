from functools import partial
from typing import final

from modstack.artifacts import Artifact
from modstack.core import SerializableModule
from modstack.query.retrievers import VoidIndexQuery
from modstack.typing import Effect, Effects

class GraphRetriever(SerializableModule[VoidIndexQuery, list[Artifact]]):
    @final
    def forward(self, query: VoidIndexQuery, **kwargs) -> Effect[list[Artifact]]:
        return Effects.From(
            invoke=partial(self._invoke, query, **kwargs),
            ainvoke=partial(self._ainvoke, query, **kwargs)
        )

    def _invoke(self, query: VoidIndexQuery, **kwargs) -> list[Artifact]:
        pass

    async def _ainvoke(self, query: VoidIndexQuery, **kwargs) -> list[Artifact]:
        pass