import io
import logging

from pypdf import PdfReader

from modstack.core.artifacts import ByteStream, Utf8Artifact
from modstack.core.modules import Modules
from modstack.core.utils.dicts import normalize_metadata
from modstack.core.utils.func import tzip
from modstack.pypdf import PyPDFToText
from modstack.pypdf.converter import _DefaultConverter

logger = logging.getLogger(__name__)

class PyPDF(Modules.Sync[PyPDFToText, list[Utf8Artifact]]):
    def _invoke(self, data: PyPDFToText, **kwargs) -> list[Utf8Artifact]:
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