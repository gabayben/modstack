from typing import Any

from modstack.contracts import Contract
from modstack.typing import ArtifactSource

class ConvertTextFile(Contract):
    sources: list[ArtifactSource]
    metadata: dict[str, Any] | list[dict[str, Any]] | None = None

class MarkdownToText(Contract):
    sources: list[ArtifactSource]
    metadata: dict[str, Any] | list[dict[str, Any]] | None = None

class HtmlToText(Contract):
    sources: list[ArtifactSource]
    metadata: dict[str, Any] | list[dict[str, Any]] | None = None

class PDFToText(Contract):
    sources: list[ArtifactSource]
    metadata: dict[str, Any] | list[dict[str, Any]] | None = None