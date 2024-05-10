from typing import Any, Protocol, Self

from pypdf import PdfReader

from modstack.typing import TextArtifact

class PyPDFConverter(Protocol):
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        pass

    def to_dict(self) -> dict[str, Any]:
        pass

    def convert(self, reader: PdfReader) -> TextArtifact:
        pass