from modstack.ai import Embedder
from modstack.artifacts import Artifact
from modstack.typing import Embedding

def embed_artifacts(
    embedder: Embedder,
    artifacts: list[Artifact],
    **kwargs
) -> dict[str, Embedding]:
    pass