from hashlib import sha256
import re
from typing import Optional

from modstack.artifacts import Artifact, TextArtifact
from modstack.modules import ArtifactTransform, Module, coerce_to_module, module
from modstack.stores.artifact import InjestionCache
from modstack.typing import MetadataType
from modstack.utils.dicts import normalize_metadata
from modstack.utils.func import tzip

def run_transformations(
    artifacts: list[Artifact],
    transformations: list[ArtifactTransform],
    cache: Optional[InjestionCache] = None,
    cache_collection: Optional[str] = None,
    in_place: bool = True
) -> list[Artifact]:
    if not in_place:
        artifacts = list(artifacts)
    for transformation in transformations:
        transformation = coerce_to_module(transformation)
        if cache:
            hash_ = get_transformation_hash(artifacts, transformation)
            cached_data = cache.get(hash_, collection=cache_collection)
            if cached_data is not None:
                artifacts = cached_data
            else:
                artifacts = transformation.invoke(artifacts)
                cache.put(hash_, artifacts, collection=cache_collection)
        else:
            artifacts = transformation.invoke(artifacts)
    return artifacts

async def arun_transformations(
    artifacts: list[Artifact],
    transformations: list[ArtifactTransform],
    cache: Optional[InjestionCache] = None,
    cache_collection: Optional[str] = None,
    in_place: bool = True
) -> list[Artifact]:
    if not in_place:
        artifacts = list(artifacts)
    for transformation in transformations:
        transformation = coerce_to_module(transformation)
        if cache:
            hash_ = get_transformation_hash(artifacts, transformation)
            cached_data = await cache.aget(hash_, collection=cache_collection)
            if cached_data is not None:
                artifacts = cached_data
            else:
                artifacts = await transformation.ainvoke(artifacts)
                await cache.aput(hash_, artifacts, collection=cache_collection)
        else:
            artifacts = await transformation.ainvoke(artifacts)
    return artifacts

def get_transformation_hash(
    artifacts: list[Artifact],
    transformation: Module[list[Artifact], list[Artifact]]
) -> str:
    artifacts_str = ''.join(str(artifact) for artifact in artifacts)
    transformation_str = _remove_unstable_values(str(transformation))
    return sha256((artifacts_str + transformation_str).encode('utf8')).hexdigest()

def _remove_unstable_values(s: str) -> str:
    return re.sub(r'<[\w\s_. ]+ at 0x[a-z0-9]+>', '', s)

@module
def to_text_artifacts(
    content: list[str],
    metadata: Optional[MetadataType] = None,
    **kwargs
) -> list[TextArtifact]:
    metadata = normalize_metadata(metadata, len(content))
    artifacts: list[TextArtifact] = []
    for text, md in tzip(content, metadata):
        artifacts.append(TextArtifact(text, metadata=md))
    return artifacts