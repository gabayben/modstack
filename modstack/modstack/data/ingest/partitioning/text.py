from modstack.artifacts import Artifact, ArtifactSource
from modstack.modules import module

@module
def text_partitioner(source: ArtifactSource, **kwargs) -> list[Artifact]:
    pass