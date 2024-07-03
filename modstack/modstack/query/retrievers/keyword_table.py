from collections import defaultdict
from functools import partial
import logging
from typing import Optional, final

from modstack.artifacts import Artifact
from modstack.core import Module, ModuleLike, SerializableModule, coerce_to_module
from modstack.query.retrievers import KeywordTableQuery
from modstack.query.structs import KeywordTable
from modstack.typing import Effect, Effects

logger = logging.getLogger(__name__)

class KeywordTableRetriever(SerializableModule[KeywordTableQuery, list[Artifact]]):
    _keyword_extractor: Module[Artifact, set[str]]

    def __init__(
        self,
        keyword_extractor: Optional[ModuleLike[Artifact, set[str]]] = None,
        num_chunks_per_query: int = 10,
        **kwargs
    ):
        super().__init__(**kwargs)
        self._keyword_extractor = coerce_to_module(keyword_extractor) if keyword_extractor else None
        self.num_chunks_per_query = num_chunks_per_query

    @final
    def forward(self, query: KeywordTableQuery, **kwargs) -> Effect[list[Artifact]]:
        return Effects.From(
            invoke=partial(self._invoke, query, **kwargs),
            ainvoke=partial(self._ainvoke, query, **kwargs)
        )

    def _invoke(self, query: KeywordTableQuery, **kwargs) -> list[Artifact]:
        logger.info(f'> Starting query: {str(query.value)}')
        keyword_extractor = self._keyword_extractor or query.index.keyword_extractor
        keywords = keyword_extractor.invoke(query.value, **kwargs)
        chunk_ids = self._extract_chunk_ids(query.index.struct, keywords)
        return query.index.artifact_store.get_many(chunk_ids, **kwargs)

    async def _ainvoke(self, query: KeywordTableQuery, **kwargs) -> list[Artifact]:
        logger.info(f'> Starting query: {str(query.value)}')
        keyword_extractor = self._keyword_extractor or query.index.keyword_extractor
        keywords = await keyword_extractor.ainvoke(query.value, **kwargs)
        chunk_ids = self._extract_chunk_ids(query.index.struct, keywords)
        return await query.index.artifact_store.aget_many(chunk_ids, **kwargs)

    def _extract_chunk_ids(
        self,
        struct: KeywordTable,
        keywords: set[str]
    ) -> list[str]:
        logger.info(f'query keywords: {keywords}')

        chunk_ids_count: dict[str, int] = defaultdict(int)
        keywords = [k for k in keywords if k in struct.keywords]
        logger.info(f'> Extracted keywords: {keywords}')

        for keyword in keywords:
            for artifact_id in struct.table[keyword]:
                chunk_ids_count[artifact_id] += 1

        sorted_chunk_ids = sorted(
            chunk_ids_count.keys(),
            key=lambda x: chunk_ids_count[x],
            reverse=True
        )
        return sorted_chunk_ids[:self.num_chunks_per_query]