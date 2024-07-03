from typing import Generic, TypeVar

from modstack.artifacts import Artifact
from modstack.query.indices import Index, KeywordTableIndex, KnowledgeGraphIndex, ListIndex, SummaryIndex
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
KnowledgeGraphQuery = IndexQuery[KnowledgeGraphIndex]
ListIndexQuery = IndexQuery[ListIndex]
SummaryIndexQuery = IndexQuery[SummaryIndex]