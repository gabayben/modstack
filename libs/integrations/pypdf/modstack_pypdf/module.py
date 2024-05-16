import io
import logging
from typing import Any

from pypdf import PdfReader

from modstack.endpoints import endpoint
from modstack.modules import Module
from modstack.typing import ArtifactSource, ByteStream, Utf8Artifact
from modstack.utils.dicts import normalize_metadata
from modstack.utils.func import tzip
from modstack_pypdf import PyPDFConverter
from modstack_pypdf.converter import _DefaultConverter

logger = logging.getLogger(__name__)

class PyPDF(Module):
    @endpoint
    def pdf_to_text(
        self,
        sources: list[ArtifactSource],
        metadata: dict[str, Any] | list[dict[str, Any]] | None = None,
        converter: PyPDFConverter | None = None,
        **kwargs
    ) -> list[Utf8Artifact]:
        metadata = normalize_metadata(metadata, len(sources))
        converter = converter or _DefaultConverter()
        results: list[Utf8Artifact] = []

        for source, md in tzip(sources, metadata):
            try:
                bytestream = ByteStream.from_source(source, md)
            except Exception as e:
                logger.warning(f'Could not read {source}. Skipping it. Error: {e}.')
                continue
            try:
                reader = PdfReader(io.BytesIO(bytes(bytestream)))
                results.append(converter.convert(reader))
            except Exception as e:
                logger.warning(f'Could not read {source} and convert it to TextArtifact. Skipping it. Error: {e}.')

        return results