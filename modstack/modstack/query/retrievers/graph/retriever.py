from functools import partial
from typing import final

from modstack.artifacts import Artifact
from modstack.core import SerializableModule, coerce_to_module
from modstack.query.indices import GraphIndex
from modstack.query.retrievers import GraphIndexQuery, IndexRetriever, IndexRetrieverLike
from modstack.typing import Effect, Effects

class GraphRetriever(SerializableModule[GraphIndexQuery, list[Artifact]]):
    sub_retrievers: list[IndexRetriever[GraphIndex]]
    num_workers: int

    def __init__(
        self,
        sub_retrievers: list[IndexRetrieverLike[GraphIndex]],
        num_workers: int = 4,
        **kwargs
    ):
        super().__init__(
            sub_retrievers=[coerce_to_module(retriever) for retriever in sub_retrievers],
            num_workers=num_workers,
            **kwargs
        )

    @final
    def forward(self, query: GraphIndexQuery, **kwargs) -> Effect[list[Artifact]]:
        return Effects.From(
            invoke=partial(self._invoke, query, **kwargs),
            ainvoke=partial(self._ainvoke, query, **kwargs)
        )

    def _invoke(self, query: GraphIndexQuery, **kwargs) -> list[Artifact]:
        pass

    async def _ainvoke(self, query: GraphIndexQuery, **kwargs) -> list[Artifact]:
        pass