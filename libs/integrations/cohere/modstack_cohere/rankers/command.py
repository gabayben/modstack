from modstack.commands import Command
from modstack.typing import Utf8Artifact

class CohereRank(Command[list[Utf8Artifact]]):
    query: str
    artifacts: list[Utf8Artifact]
    top_k: int | None = None
    max_chunks_per_doc: int | None = None
    meta_fields_to_embed: list[str] | None = None
    metadata_seperator: str | None = None

    @classmethod
    def name(cls) -> str:
        return 'cohere_rank'