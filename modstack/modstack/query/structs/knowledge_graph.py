from typing import Union

from pydantic import Field

from modstack.artifacts import Artifact
from modstack.query.structs import IndexStruct
from modstack.typing import Embedding

TripletLike = Union[str, tuple[str, str, str]]

class KnowledgeGraph(IndexStruct):
    table: dict[str, set[str]] = Field(default_factory=dict)
    embedding_dict: dict[str, Embedding] = Field(default_factory=dict)

    @property
    def keywords(self) -> list[str]:
        return list(self.table.keys())

    @property
    def chunk_ids(self) -> set[str]:
        return set.union(*self.table.values())

    def add_embedding(self, triplet: TripletLike, embedding: Embedding) -> None:
        self.embedding_dict[str(triplet)] = embedding

    def add_chunk(self, chunk: Artifact, keywords: list[str]) -> None:
        for keyword in keywords:
            if keyword not in self.table:
                self.table[keyword] = set()
            self.table[keyword].add(chunk.id)

    def search_chunks_by_keyword(self, keyword: str) -> list[str]:
        if keyword not in self.table:
            return []
        return list(self.table[keyword])