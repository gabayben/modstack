from typing import Any

from modstack.contracts import Contract
from modstack.typing import ArtifactSource, Utf8Artifact

class ConvertTextFile(Contract[list[Utf8Artifact]]):
    sources: list[ArtifactSource]
    metadata: dict[str, Any] | list[dict[str, Any]] | None = None

    @classmethod
    def name(cls) -> str:
        return 'convert_text_file'

class MarkdownToText(Contract):
    sources: list[ArtifactSource]
    metadata: dict[str, Any] | list[dict[str, Any]] | None = None

class HtmlToText(Contract):
    sources: list[ArtifactSource]
    metadata: dict[str, Any] | list[dict[str, Any]] | None = None

class PDFToText(Contract):
    sources: list[ArtifactSource]
    metadata: dict[str, Any] | list[dict[str, Any]] | None = None