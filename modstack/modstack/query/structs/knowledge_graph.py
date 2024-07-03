from pydantic import Field

from modstack.query.structs import IndexStruct
from modstack.typing import Embedding

class KnowledgeGraph(IndexStruct):
    table: dict[str, set[str]] = Field(default_factory=dict)
    embedding_dict: dict[str, Embedding] = Field(default_factory=dict)