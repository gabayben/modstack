from typing import Generic, TypeVar

from modstack.artifacts import Artifact
from modstack.core import Module, ModuleLike
from modstack.query.indices import GraphIndex, Index, KeywordTableIndex, ListIndex, SummaryIndex
from modstack.typing import Schema

_INDEX = TypeVar('_INDEX', bound=Index)

class IndexQuery(Schema, Generic[_INDEX]):
    value: Artifact
    index: _INDEX

    def __init__(
        self,
        value: Artifact,
        index: _INDEX,
        **kwargs
    ):
        super().__init__(value=value, index=index, **kwargs)

GraphIndexQuery = IndexQuery[GraphIndex]
KeywordTableQuery = IndexQuery[KeywordTableIndex]
ListIndexQuery = IndexQuery[ListIndex]
SummaryIndexQuery = IndexQuery[SummaryIndex]
IndexRetrieverLike = ModuleLike[IndexQuery[_INDEX], list[Artifact]]
IndexRetriever = Module[IndexQuery[_INDEX], list[Artifact]]