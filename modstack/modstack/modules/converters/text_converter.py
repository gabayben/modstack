import logging

from modstack.artifacts import ArtifactSource, TextArtifact, Utf8Artifact
from modstack.modules import Modules
from modstack.typing import MetadataType
from modstack.utils.dicts import normalize_metadata
from modstack.utils.func import tzip

logger = logging.getLogger(__name__)

class TextConverter(Modules.Sync[list[ArtifactSource], list[Utf8Artifact]]):
    def _invoke(
        self,
        sources: list[ArtifactSource],
        metadata: MetadataType | None = None,
        **kwargs
    ) -> list[Utf8Artifact]:
        metadata = normalize_metadata(metadata, len(sources))
        results: list[TextArtifact] = []

        for source, md in tzip(sources, metadata):
            try:
                results.append(TextArtifact.from_source(source, md))
            except Exception as e:
                logger.warning(f'Could not read {source}. Skipping it. Error: {e}.')

        return results