from typing import Any, Sequence

import cohere

from modstack.contracts import TextEmbeddingRequest

class CohereTextEmbeddingRequest(TextEmbeddingRequest):
    model: str | None = None
    input_type: cohere.EmbedInputType | None = None
    embedding_types: Sequence[cohere.EmbeddingType] | None = None
    truncate: cohere.EmbedRequestTruncate | Any | None = None
    request_options: cohere.client.RequestOptions | None = None
    meta_fields_to_embed: list[str] | None = None
    embedding_seperator: str | None = None
    batch_size: int | None = None