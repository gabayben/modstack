from typing import Optional

from modstack.artifacts import Artifact, ArtifactSource
from modstack.data.ingest import default_partition_options
from modstack.core import module

@module
def text_partitioner(source: ArtifactSource, **kwargs) -> list[Artifact]:
    options = default_partition_options(kwargs)
    text: Optional[str] = None
    if isinstance(source, Artifact):
        text = str(source)
        if text.strip() == '':
            return []