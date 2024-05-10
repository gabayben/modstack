import io
import logging
from typing import Any

from tika import parser

from modstack.commands import PDFToText
from modstack.core import Module, command
from modstack.typing import ArtifactSource, ByteStream, TextArtifact
from modstack.utils.dicts import normalize_metadata
from modstack.utils.func import zip2
from modstack_tika import TikaToText

logger = logging.getLogger(__name__)

class Tika(Module):
    def __init__(self, tika_url: str = 'http://localhost:9998/tika', **kwargs):
        super().__init__(**kwargs)
        self.tika_url = tika_url

    @command(TikaToText)
    def tika_to_text(
        self,
        sources: list[ArtifactSource],
        metadata: dict[str, Any] | list[dict[str, Any]] | None = None,
        **kwargs
    ) -> list[TextArtifact]:
        metadata = normalize_metadata(metadata, len(sources))
        results: list[TextArtifact] = []

        for source, md in zip2(sources, metadata):
            try:
                bytestream = ByteStream.from_source(source, md)
            except Exception as e:
                logger.warning(f'Could not read {source}. Skipping it. Error: {e}.')
                continue
            try:
                text = parser.from_buffer(io.BytesIO(bytes(bytestream)), serverEndpoint=self.tika_url)['content']
            except Exception as e:
                logger.warning(f'Failed to extract text from {source}. Skipping it. Error: {e}.')
                continue
            results.append(TextArtifact(text))

        return results

    @command(PDFToText)
    def pdf_to_text(
        self,
        sources: list[ArtifactSource],
        metadata: dict[str, Any] | list[dict[str, Any]] | None = None,
        **kwargs
    ) -> list[TextArtifact]:
        return self.tika_to_text(sources, metadata, **kwargs)