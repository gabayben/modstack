from abc import ABC, abstractmethod

from pypdf import PdfReader

from modstack.artifacts import TextArtifact, Utf8Artifact
from modstack.typing import Serializable

class PyPDFExtractor(Serializable, ABC):
    @abstractmethod
    def convert(self, reader: PdfReader) -> list[Utf8Artifact]:
        pass

class _DefaultExtractor(Serializable, PyPDFExtractor):
    def convert(self, reader: PdfReader) -> list[Utf8Artifact]:
        return [
            TextArtifact(
                page.extract_text(),
                metadata={'page': page.page_number, **reader.metadata}
            )
            for page in reader.pages
        ]