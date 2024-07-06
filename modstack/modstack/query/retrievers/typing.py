from typing import Generic, TypeVar

from modstack.artifacts import Artifact
from modstack.query.indices import Index, KeywordTableIndex, ListIndex, SummaryIndex
from modstack.query.structs import VoidStruct
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

KeywordTableQuery = IndexQuery[KeywordTableIndex]
ListIndexQuery = IndexQuery[ListIndex]
SummaryIndexQuery = IndexQuery[SummaryIndex]
VoidIndexQuery= IndexQuery[VoidStruct]