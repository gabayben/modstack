from collections import defaultdict
from functools import partial
import logging
from typing import Optional

from modstack.artifacts import Artifact
from modstack.core import Module, ModuleLike, SerializableModule, coerce_to_module
from modstack.query.indices import KeywordTableIndex
from modstack.query.structs import KeywordTable
from modstack.typing import Effect, Effects

logger = logging.getLogger(__name__)

class KeywordTableRetriever(SerializableModule[Artifact, list[Artifact]]):
    _keyword_extractor: Module[Artifact, set[str]]

    @property
    def index(self) -> KeywordTableIndex:
        return self._index

    @property
    def struct(self) -> KeywordTable:
        return self.index.struct

    def __init__(
        self,
        index: KeywordTableIndex,
        keyword_extractor: Optional[ModuleLike[Artifact, set[str]]] = None,
        num_chunks_per_query: int = 10,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._index = index
        self._keyword_extractor = (
            coerce_to_module(keyword_extractor)
            if keyword_extractor
            else self.index.keyword_extractor
        )
        self.num_chunks_per_query = num_chunks_per_query

    def forward(self, query: Artifact, **kwargs) -> Effect[list[Artifact]]:
        return Effects.From(
            invoke=partial(self._invoke, query, **kwargs),
            ainvoke=partial(self._ainvoke, query, **kwargs)
        )

    def _invoke(self, query: Artifact, **kwargs) -> list[Artifact]:
        logger.info(f'> Starting query: {str(query)}')
        keywords = self._keyword_extractor.invoke(query, **kwargs)
        chunk_ids = self._extract_chunk_ids(keywords)
        return self.index.artifact_store.get_many(chunk_ids, **kwargs)

    async def _ainvoke(self, query: Artifact, **kwargs) -> list[Artifact]:
        logger.info(f'> Starting query: {str(query)}')
        keywords = await self._keyword_extractor.ainvoke(query, **kwargs)
        chunk_ids = self._extract_chunk_ids(keywords)
        return await self.index.artifact_store.aget_many(chunk_ids, **kwargs)

    def _extract_chunk_ids(self, keywords: set[str]) -> list[str]:
        logger.info(f'query keywords: {keywords}')

        chunk_ids_count: dict[str, int] = defaultdict(int)
        keywords = [k for k in keywords if k in self.struct.keywords]
        logger.info(f'> Extracted keywords: {keywords}')

        for keyword in keywords:
            for artifact_id in self.struct.table[keyword]:
                chunk_ids_count[artifact_id] += 1

        sorted_chunk_ids = sorted(
            chunk_ids_count.keys(),
            key=lambda x: chunk_ids_count[x],
            reverse=True
        )
        return sorted_chunk_ids[:self.num_chunks_per_query]