import io
import logging
from typing import Any, Iterator

from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTPage, LTTextContainer

from modstack.core.artifacts import ByteStream, TextArtifact, Utf8Artifact
from modstack.core.modules import Modules
from modstack.core.utils.dicts import normalize_metadata
from modstack.core.utils.func import tzip
from modstack.pdfminer import PDFMinerToText

logger = logging.getLogger(__name__)

class PDFMiner(Modules.Sync[PDFMinerToText, list[Utf8Artifact]]):
    def _invoke(self, data: PDFMinerToText, **kwargs) -> list[Utf8Artifact]:
        metadata = normalize_metadata(data.metadata, len(data.sources))
        results: list[TextArtifact] = []

        layout_params = data.layout_params or LAParams(
            line_overlap=0.5,
            char_margin=2.,
            line_margin=0.5,
            word_margin=0.1,
            boxes_flow=0.5,
            detect_vertical=True,
            all_texts=False
        )

        for source, md in tzip(data.sources, metadata):
            try:
                bytestream = ByteStream.from_source(source, md)
            except Exception as e:
                logger.warning(f'Could not read {source}. Skipping it.')
                logger.exception(e)
                continue
            try:
                pages = extract_pages(io.BytesIO(bytes(bytestream)), laparams=layout_params)
                results.append(self._convert(pages, bytestream.metadata))
            except Exception as e:
                logger.warning(f'Could not read {source} and convert it to TextArtifact. Skipping it.')
                logger.exception(e)

        return results

    def _convert(self, pages: Iterator[LTPage], metadata: dict[str, Any]) -> TextArtifact:
        texts: list[str] = []
        for page in pages:
            text = ''
            for container in page:
                if isinstance(container, LTTextContainer):
                    text += container.get_text()
            texts.append(text)
        return TextArtifact('\f'.join(texts), metadata=metadata)