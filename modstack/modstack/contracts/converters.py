from typing import Any

from modstack.contracts import Contract
from modstack.typing import ArtifactSource, Utf8Artifact

class ConvertTextFile(Contract[list[Utf8Artifact]]):
    sources: list[ArtifactSource]
    metadata: dict[str, Any] | list[dict[str, Any]] | None = None

    @classmethod
    def name(cls) -> str:
        return 'convert_text_file'

class MarkdownToText(Contract[list[Utf8Artifact]]):
    sources: list[ArtifactSource]
    metadata: dict[str, Any] | list[dict[str, Any]] | None = None

    @classmethod
    def name(cls) -> str:
        return 'markdown_to_text'

class HtmlToText(Contract[list[Utf8Artifact]]):
    sources: list[ArtifactSource]
    metadata: dict[str, Any] | list[dict[str, Any]] | None = None

    @classmethod
    def name(cls) -> str:
        return 'html_to_text'

class PDFToText(Contract[list[Utf8Artifact]]):
    sources: list[ArtifactSource]
    metadata: dict[str, Any] | list[dict[str, Any]] | None = None

    @classmethod
    def name(cls) -> str:
        return 'pdf_to_text'

class JinjaMapping(Contract[Any]):
    context: Any

    @classmethod
    def name(cls) -> str:
        return 'jinja_mapping'