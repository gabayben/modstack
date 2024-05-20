from typing import Any, Sequence

import cohere
import numpy as np

from modstack.auth import Secret
from modstack.contracts import EmbedTextResponse

from modstack.modules import Modules
from modstack.utils.func import tzip
from modstack_cohere.embedders import CohereEmbedText
from modstack_cohere.typing import OMIT

_EMBED_RESPONSE = cohere.EmbedResponse_EmbeddingsFloats | cohere.EmbedResponse_EmbeddingsByType

class CohereTextEmbedder(Modules.Async[CohereEmbedText, EmbedTextResponse]):
    def __init__(
        self,
        token: Secret = Secret.from_env_var(['COHERE_API_KEY', 'CO_API_KEY']),
        base_url: str = 'https://api.cohere.com',
        use_async_client: bool = True,
        timeout: int = 120,
        model: str = 'embedders-english-v2.0',
        input_type: cohere.EmbedInputType | None = 'search_document',
        embedding_types: Sequence[cohere.EmbeddingType] | None = OMIT,
        truncate: cohere.EmbedRequestTruncate | Any = 'END',
        request_options: cohere.client.RequestOptions | None = None,
        meta_fields_to_embed: list[str] | None = None,
        embedding_seperator: str = '\n',
        batch_size: int = 32
    ):
        super().__init__()

        if use_async_client:
            self.async_client = cohere.AsyncClient(
                api_key=token.resolve_value(),
                base_url=base_url,
                client_name='modstack',
                timeout=timeout
            )
        else:
            self.client = cohere.Client(
                api_key=token.resolve_value(),
                base_url=base_url,
                client_name='modstack',
                timeout=timeout
            )

        self.model = model
        self.input_type = input_type
        self.embedding_types = embedding_types
        self.truncate = truncate
        self.request_options = request_options or {}
        self.meta_fields_to_embed = meta_fields_to_embed or []
        self.embedding_seperator = embedding_seperator
        self.batch_size = batch_size

    async def _ainvoke(self, data: CohereEmbedText) -> EmbedTextResponse:
        if not data.artifacts:
            return EmbedTextResponse(artifacts=[])

        model = data.model or self.model
        input_type = data.input_type or self.input_type
        embedding_types = data.embedding_types or self.embedding_types
        truncate = data.truncate or self.truncate
        request_options = {**self.request_options, **(data.request_options or {})}
        meta_fields_to_embed = list({*self.meta_fields_to_embed, *(data.meta_fields_to_embed or [])})
        batch_size = data.batch_size or self.batch_size

        texts_to_embed: list[str] = []
        for artifact in data.artifacts:
            meta_values_to_embed = [str(artifact.metadata[key]) for key in meta_fields_to_embed if
                                    artifact.metadata.get(key, None)]
            texts_to_embed.append(
                self.embedding_seperator.join([*meta_values_to_embed, str(artifact)])
            )

        all_embeddings: list[list[float]] = []
        metadata: dict[str, Any] = {}

        if hasattr(self, 'async_client'):
            response = await self.async_client.embed(
                texts=texts_to_embed,
                model=model,
                input_type=input_type,
                embedding_types=embedding_types,
                truncate=truncate,
                request_options=request_options
            )
            for embedding in response.embeddings:
                all_embeddings.append(embedding)
            if response.meta is not None:
                metadata = response.meta
        else:
            for i in range(0, len(texts_to_embed), batch_size):
                batch = texts_to_embed[i: i + batch_size]
                response = self.client.embed(
                    texts=batch,
                    model=model,
                    input_type=input_type,
                    embedding_types=embedding_types,
                    truncate=truncate,
                    request_options=request_options
                )
                for embedding in response.embeddings:
                    all_embeddings.append(embedding)
                if response.meta is not None:
                    metadata = response.meta

        for artifact, embedding in tzip(data.artifacts, all_embeddings):
            artifact.embedding = np.asarray(embedding)

        return EmbedTextResponse(data.artifacts, metadata=metadata)