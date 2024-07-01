import logging
from typing import ClassVar

import cohere

from modstack.artifacts import Artifact
from modstack.cohere.rankers import CohereRankRequest
from modstack.auth import Secret
from modstack.core import Modules
from modstack.utils.func import tzip

logger = logging.getLogger(__name__)

class CohereRanker(Modules.Async[CohereRankRequest, list[Artifact]]):
    MAX_NUM_DOCS_FOR_COHERE_RANKER: ClassVar[int] = 1000

    def __init__(
        self,
        token: Secret = Secret.from_env_var(['COHERE_API_KEY', 'CO_API_KEY']),
        base_url: str = 'https://api.cohere.com',
        model: str = 'rerank-english-v2.0',
        top_k: int = 10,
        max_chunks_per_doc: int | None = None,
        meta_fields_to_embed: list[str] | None = None,
        metadata_seperator: str = '\n'
    ):
        super().__init__()
        self.client = cohere.AsyncClient(
            api_key=token.resolve_value(),
            base_url=base_url,
            client_name='modstack'
        )
        self.model = model
        self.top_k = top_k
        self.max_chunks_per_doc = max_chunks_per_doc
        self.meta_fields_to_embed = meta_fields_to_embed or []
        self.metadata_seperator = metadata_seperator

    async def _ainvoke(
        self,
        data: CohereRankRequest,
        top_k: int | None = None,
        max_chunks_per_doc: int | None = None,
        meta_fields_to_embed: list[str] | None = None,
        metadata_seperator: str | None = None,
        **kwargs
    ) -> list[Artifact]:
        if not data.query or not data.artifacts:
            return []

        top_k = top_k or self.top_k
        if top_k <= 0:
            raise ValueError(f'top_k must be greater than 0, but got {top_k}.')

        max_chunks_per_doc = max_chunks_per_doc or self.max_chunks_per_doc
        max_chunks_per_doc = min(max_chunks_per_doc, 10000) if max_chunks_per_doc else None
        meta_fields_to_embed = list({*self.meta_fields_to_embed, *(meta_fields_to_embed or [])})
        metadata_seperator = metadata_seperator or self.metadata_seperator

        cohere_input_docs = []
        for artifact in data.artifacts:
            meta_values_to_embed = [str(artifact.metadata[key]) for key in meta_fields_to_embed if
                                    artifact.metadata.get(key, None)]
            cohere_input_docs.append(
                metadata_seperator.join([*meta_values_to_embed, str(artifact)])
            )

        if len(cohere_input_docs) > self.MAX_NUM_DOCS_FOR_COHERE_RANKER:
            logger.warning(
                f"The Cohere reranking endpoint only supports {self.MAX_NUM_DOCS_FOR_COHERE_RANKER} documents."
                + f"The number of documents has been truncated to {self.MAX_NUM_DOCS_FOR_COHERE_RANKER}"
                + f"from {len(cohere_input_docs)}."
            )
            cohere_input_docs = cohere_input_docs[:self.MAX_NUM_DOCS_FOR_COHERE_RANKER]

        response = await self.client.rerank(
            model=self.model,
            query=data.query,
            documents=cohere_input_docs,
            top_n=top_k,
            max_chunks_per_doc=max_chunks_per_doc
        )

        indices: list[int] = []
        scores: list[float] = []
        for result in response.results:
            indices.append(result.index)
            scores.append(result.relevance_score)

        sorted_artifacts: list[Artifact] = []
        for index, score in tzip(indices, scores):
            artifact = data.artifacts[index]
            artifact.score = score
            sorted_artifacts.append(artifact)

        return sorted_artifacts