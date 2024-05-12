import io
import logging
from typing import Any, Iterator

from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTPage, LTTextContainer

from modstack.commands import PDFToText, command
from modstack.modules import Module
from modstack.typing import ArtifactSource, ByteStream, TextArtifact
from modstack.utils.dicts import normalize_metadata
from modstack.utils.func import tzip
from modstack_pdfminer import PDFMinerToText

logger = logging.getLogger(__name__)

class PDFMiner(Module):
    @command(PDFToText)
    def to_text(
        self,
        sources: list[ArtifactSource],
        metadata: dict[str, Any] | list[dict[str, Any]] | None = None,
        **kwargs
    ) -> list[TextArtifact]:
        return self.pdfminer_to_text(sources, metadata=metadata, **kwargs)

    @command(PDFMinerToText)
    def pdfminer_to_text(
        self,
        sources: list[ArtifactSource],
        metadata: dict[str, Any] | list[dict[str, Any]] | None = None,
        layout_params: LAParams | None = None,
        **kwargs
    ) -> list[TextArtifact]:
        metadata = normalize_metadata(metadata, len(sources))
        results: list[TextArtifact] = []

        layout_params = layout_params or LAParams(
            line_overlap=0.5,
            char_margin=2.,
            line_margin=0.5,
            word_margin=0.1,
            boxes_flow=0.5,
            detect_vertical=True,
            all_texts=False
        )

        for source, md in tzip(sources, metadata):
            try:
                bytestream = ByteStream.from_source(source, md)
            except Exception as e:
                logger.warning(f'Could not read {source}. Skipping it. Error: {e}.')
                continue
            try:
                pages = extract_pages(io.BytesIO(bytes(bytestream)), laparams=layout_params)
                results.append(self._convert(pages, bytestream.metadata))
            except Exception as e:
                logger.warning(f'Could not read {source} and convert it to TextArtifact. Skipping it. Error: {e}.')

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