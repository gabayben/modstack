import io
import logging
from typing import Optional

from pypdf import PdfReader

from modstack.artifacts import ArtifactSource, ByteStream, Utf8Artifact
from modstack.modules import Modules
from modstack.typing import MetadataType
from modstack.utils.dicts import normalize_metadata
from modstack.utils.func import tzip
from modstack.pypdf.converter import PyPDFExtractor, _DefaultExtractor

logger = logging.getLogger(__name__)

class PyPDFConverter(Modules.Sync[list[ArtifactSource], list[Utf8Artifact]]):
    def _invoke(
        self,
        sources: list[ArtifactSource],
        metadata: Optional[MetadataType] = None,
        converter: PyPDFExtractor | None = None,
        **kwargs
    ) -> list[Utf8Artifact]:
        metadata = normalize_metadata(metadata, len(sources))
        converter = converter or _DefaultExtractor()
        results: list[Utf8Artifact] = []

        for source, md in tzip(sources, metadata):
            try:
                bytestream = ByteStream.from_source(source, md)
            except Exception as e:
                logger.warning(f'Could not read {source}. Skipping it.')
                logger.exception(e)
                continue
            try:
                reader = PdfReader(io.BytesIO(bytes(bytestream)))
                results.extend(converter.convert(reader))
            except Exception as e:
                logger.warning(f'Could not read {source} and convert it to TextArtifact. Skipping it.')
                logger.exception(e)

        return results