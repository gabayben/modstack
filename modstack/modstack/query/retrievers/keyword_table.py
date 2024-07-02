from functools import partial
from typing import Optional

from modstack.artifacts import Artifact
from modstack.core import Module, ModuleLike, SerializableModule, coerce_to_module
from modstack.query.indices import KeywordTableIndex
from modstack.typing import Effect, Effects

class KeywordTableRetriever(SerializableModule[Artifact, list[Artifact]]):
    _keyword_extractor: Module[Artifact, set[str]]

    @property
    def index(self) -> KeywordTableIndex:
        return self._index

    def __init__(
        self,
        index: KeywordTableIndex,
        keyword_extractor: Optional[ModuleLike[Artifact, set[str]]] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._index = index
        self._keyword_extractor = (
            coerce_to_module(keyword_extractor)
            if keyword_extractor
            else self.index.keyword_extractor
        )

    def forward(self, query: Artifact, **kwargs) -> Effect[list[Artifact]]:
        return Effects.From(
            invoke=partial(self._invoke, query, **kwargs),
            ainvoke=partial(self._ainvoke, query, **kwargs)
        )

    def _invoke(self, query: Artifact, **kwargs) -> list[Artifact]:
        pass

    async def _ainvoke(self, query: Artifact, **kwargs) -> list[Artifact]:
        pass