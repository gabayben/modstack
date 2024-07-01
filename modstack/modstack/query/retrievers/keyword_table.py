from functools import partial
from typing import Optional

from modstack.artifacts import Artifact
from modstack.core import Module, ModuleLike, SerializableModule, coerce_to_module
from modstack.query.common import simple_keyword_extractor
from modstack.query.structs import KeywordTable
from modstack.typing import Effect, Effects

class KeywordTableRetriever(SerializableModule[Artifact, list[Artifact]]):
    _keyword_extractor: Module[Artifact, set[str]]

    @property
    def index(self) -> KeywordTable:
        return self._index

    def __init__(
        self,
        index: KeywordTable,
        keyword_extractor: Optional[ModuleLike[Artifact, set[str]]] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._index = index
        self._keyword_extractor = coerce_to_module(keyword_extractor) if keyword_extractor else simple_keyword_extractor

    def forward(self, artifact: Artifact, **kwargs) -> Effect[list[Artifact]]:
        return Effects.From(
            invoke=partial(self._invoke, artifact, **kwargs),
            ainvoke=partial(self._ainvoke, artifact, **kwargs)
        )

    def _invoke(self, artifact: Artifact, **kwargs) -> list[Artifact]:
        pass

    async def _ainvoke(self, artifact: Artifact, **kwargs) -> list[Artifact]:
        pass