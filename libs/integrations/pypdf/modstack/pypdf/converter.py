from abc import ABC, abstractmethod

from pypdf import PdfReader

from modstack.core.typing import Serializable, TextArtifact, Utf8Artifact

class PyPDFConverter(Serializable, ABC):
    @abstractmethod
    def convert(self, reader: PdfReader) -> Utf8Artifact:
        pass

class _DefaultConverter(Serializable, PyPDFConverter):
    def convert(self, reader: PdfReader) -> Utf8Artifact:
        return TextArtifact('\f'.join([page.extract_text() for page in reader.pages]))