import logging

from modstack.core.artifacts import TextArtifact, Utf8Artifact
from modstack.core.modules import Modules
from modstack.core.modules.converters import ToText
from modstack.core.utils.dicts import normalize_metadata
from modstack.core.utils.func import tzip

logger = logging.getLogger(__name__)

class TextConverter(Modules.Sync[ToText, list[Utf8Artifact]]):
    def _invoke(self, data: ToText, **kwargs) -> list[Utf8Artifact]:
        metadata = normalize_metadata(data.metadata, len(data.sources))
        results: list[TextArtifact] = []

        for source, md in tzip(data.sources, metadata):
            try:
                results.append(TextArtifact.from_source(source, md))
            except Exception as e:
                logger.warning(f'Could not read {source}. Skipping it. Error: {e}.')

        return results