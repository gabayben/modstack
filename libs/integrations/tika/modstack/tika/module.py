import io
import logging

from tika import parser

from modstack.artifacts import ByteStream, TextArtifact, Utf8Artifact
from modstack.modules import Modules
from modstack.modules import ToText
from modstack.utils import normalize_metadata
from modstack.utils import tzip

logger = logging.getLogger(__name__)

class Tika(Modules.Sync[ToText, list[Utf8Artifact]]):
    def __init__(self, tika_url: str = 'http://localhost:9998/tika'):
        super().__init__()
        self.tika_url = tika_url

    def _invoke(self, data: ToText, **kwargs) -> list[Utf8Artifact]:
        metadata = normalize_metadata(data.metadata, len(data.sources))
        results: list[TextArtifact] = []

        for source, md in tzip(data.sources, metadata):
            try:
                bytestream = ByteStream.from_source(source, md)
            except Exception as e:
                logger.warning(f'Could not read {source}. Skipping it.')
                logger.exception(e)
                continue
            try:
                text = parser.from_buffer(io.BytesIO(bytes(bytestream)), serverEndpoint=self.tika_url)['content']
            except Exception as e:
                logger.warning(f'Failed to extract text from {source}. Skipping it.')
                logger.exception(e)
                continue
            results.append(TextArtifact(text))

        return results