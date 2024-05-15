import logging
from typing import Any

from modstack.containers import feature

from modstack.contracts import ConvertTextFile
from modstack.modules import Module
from modstack.typing import ArtifactSource, TextArtifact, Utf8Artifact
from modstack.utils.dicts import normalize_metadata
from modstack.utils.func import tzip

logger = logging.getLogger(__name__)

class TextConverter(Module):
    @feature(name=ConvertTextFile.name())
    def from_text_file(
        self,
        sources: list[ArtifactSource],
        metadata: dict[str, Any] | list[dict[str, Any]] | None = None,
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