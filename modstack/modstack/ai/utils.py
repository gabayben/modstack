from modstack.ai import Embedder
from modstack.artifacts import Artifact
from modstack.utils.func import tzip

def embed_query(
    embedder: Embedder,
    query: Artifact,
    **kwargs
) -> Artifact:
    if query.embedding is None:
        query.embedding = embedder.invoke([query])[0].embedding
    return query

async def aembed_query(
    embedder: Embedder,
    query: Artifact,
    **kwargs
) -> Artifact:
    if query.embedding is None:
        query.embedding = (await embedder.ainvoke([query]))[0].embedding
    return query

def embed_artifacts(
    embedder: Embedder,
    artifacts: list[Artifact],
    **kwargs
) -> list[Artifact]:
    artifacts_to_embed: list[Artifact] = []
    indices_to_embed: list[int] = []

    for idx, artifact in enumerate(artifacts):
        if artifact.embedding is None:
            artifacts_to_embed.append(artifact)
            indices_to_embed.append(idx)

    artifacts_to_embed = embedder.invoke(artifacts_to_embed, **kwargs)
    for idx, embedded_artifact in tzip(indices_to_embed, artifacts_to_embed):
        artifacts[idx].embedding = embedded_artifact.embedding

    return artifacts

async def aembed_artifacts(
    embedder: Embedder,
    artifacts: list[Artifact],
    **kwargs
) -> list[Artifact]:
    artifacts_to_embed: list[Artifact] = []
    indices_to_embed: list[int] = []

    for idx, artifact in enumerate(artifacts):
        if artifact.embedding is None:
            artifacts_to_embed.append(artifact)
            indices_to_embed.append(idx)

    artifacts_to_embed = await embedder.ainvoke(artifacts_to_embed, **kwargs)
    for idx, embedded_artifact in tzip(indices_to_embed, artifacts_to_embed):
        artifacts[idx].embedding = embedded_artifact.embedding

    return artifacts