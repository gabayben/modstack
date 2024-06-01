from modstack.core.artifacts import Utf8Artifact
from modstack.core.modules import Module, Modules
from modstack.core.modules.ai import TextEmbeddingRequest, TextEmbeddingResponse

class SemanticChunker(Modules.Sync[list[Utf8Artifact], list[Utf8Artifact]]):
    embed_model: Module[TextEmbeddingRequest, TextEmbeddingResponse]
    buffer_size: int
    breakpoint_percentile_threshold: int

    def __init__(
        self,
        embed_model: Module[TextEmbeddingRequest, TextEmbeddingResponse],
        buffer_size: int = 1,
        breakpoint_percentile_threshold: int = 95,
        **kwargs
    ):
        super().__init__(
            embed_model=embed_model,
            buffer_size=buffer_size,
            breakpoint_percentile_threshold=breakpoint_percentile_threshold,
            **kwargs
        )

    def _invoke(self, data: list[Utf8Artifact], **kwargs) -> list[Utf8Artifact]:
        pass