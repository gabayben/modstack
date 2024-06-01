from modstack.core.artifacts import Utf8Artifact
from modstack.core.typing import Serializable

class CohereRankRequest(Serializable):
    query: str
    artifacts: list[Utf8Artifact]
    top_k: int | None = None
    max_chunks_per_doc: int | None = None
    meta_fields_to_embed: list[str] | None = None
    metadata_seperator: str | None = None