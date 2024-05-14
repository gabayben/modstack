from typing import Any, Sequence, override

import cohere

from modstack.commands import EmbedText

class CohereEmbedText(EmbedText):
    model: str | None = None
    input_type: cohere.EmbedInputType | None = None
    embedding_types: Sequence[cohere.EmbeddingType] | None = None
    truncate: cohere.EmbedRequestTruncate | Any | None = None
    request_options: cohere.client.RequestOptions | None = None
    meta_fields_to_embed: list[str] | None = None
    embedding_seperator: str | None = None
    batch_size: int | None = None

    @classmethod
    @override
    def name(cls) -> str:
        return 'cohere_embed_text'