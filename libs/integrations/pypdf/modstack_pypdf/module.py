import io
import logging

from pypdf import PdfReader

from modstack.modules import Modules
from modstack.typing import ByteStream, Utf8Artifact
from modstack.utils.dicts import normalize_metadata
from modstack.utils.func import tzip
from modstack_pypdf import PyPDFToText
from modstack_pypdf.converter import _DefaultConverter

logger = logging.getLogger(__name__)

class PyPDF(Modules.Sync[PyPDFToText, list[Utf8Artifact]]):
    def _invoke(self, data: PyPDFToText) -> list[Utf8Artifact]:
        metadata = normalize_metadata(data.metadata, len(data.sources))
        converter = data.converter or _DefaultConverter()
        results: list[Utf8Artifact] = []

        for source, md in tzip(data.sources, metadata):
            try:
                bytestream = ByteStream.from_source(source, md)
            except Exception as e:
                logger.warning(f'Could not read {source}. Skipping it.')
                logger.exception(e)
                continue
            try:
                reader = PdfReader(io.BytesIO(bytes(bytestream)))
                results.append(converter.convert(reader))
            except Exception as e:
                logger.warning(f'Could not read {source} and convert it to TextArtifact. Skipping it.')
                logger.exception(e)

        return results