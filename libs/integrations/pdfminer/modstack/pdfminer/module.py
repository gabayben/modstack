import io
import logging
from typing import Any, Iterator, Optional

from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTPage, LTTextContainer

from modstack.artifacts import ArtifactSource, ByteStream, TextArtifact, Utf8Artifact
from modstack.modules import Modules
from modstack.typing import MetadataType
from modstack.utils.dicts import normalize_metadata
from modstack.utils.func import tzip

logger = logging.getLogger(__name__)

class PDFMinerConverter(Modules.Sync[list[ArtifactSource], list[Utf8Artifact]]):
    def _invoke(
        self, 
        sources: list[ArtifactSource], 
        metadata: Optional[MetadataType] = None,
        layout_params: LAParams | None = None,
        **kwargs
    ) -> list[Utf8Artifact]:
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
                logger.warning(f'Could not read {source}. Skipping it.')
                logger.exception(e)
                continue
            try:
                pages = extract_pages(io.BytesIO(bytes(bytestream)), laparams=layout_params)
                results.extend(self._convert(pages, bytestream.metadata))
            except Exception as e:
                logger.warning(f'Could not read {source} and convert it to TextArtifact. Skipping it.')
                logger.exception(e)

        return results

    def _convert(self, pages: Iterator[LTPage], metadata: dict[str, Any]) -> list[TextArtifact]:
        artifacts: list[TextArtifact] = []
        for i, page in enumerate(pages):
            text = ''
            for container in page:
                if isinstance(container, LTTextContainer):
                    text += container.get_text()
            artifacts.append(TextArtifact(text, metadata={'page': i, **metadata}))
        return artifacts