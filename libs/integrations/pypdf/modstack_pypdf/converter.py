from abc import ABC, abstractmethod

from pypdf import PdfReader

from modstack.typing import Serializable, TextArtifact

class PyPDFConverter(Serializable, ABC):
    @abstractmethod
    def convert(self, reader: PdfReader) -> TextArtifact:
        pass

class _DefaultConverter(Serializable, PyPDFConverter):
    def convert(self, reader: PdfReader) -> TextArtifact:
        return TextArtifact('\f'.join([page.extract_text() for page in reader.pages]))