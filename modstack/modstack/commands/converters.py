from typing import Any

from modstack.commands import Command
from modstack.typing import ArtifactSource, Utf8Artifact

class ToText(Command[list[Utf8Artifact]]):
    sources: list[ArtifactSource]
    metadata: dict[str, Any] | list[dict[str, Any]] | None = None

class MarkdownToText(Command[list[Utf8Artifact]]):
    sources: list[ArtifactSource]
    metadata: dict[str, Any] | list[dict[str, Any]] | None = None

class HtmlToText(Command[list[Utf8Artifact]]):
    sources: list[ArtifactSource]
    metadata: dict[str, Any] | list[dict[str, Any]] | None = None

class PDFToText(Command[list[Utf8Artifact]]):
    sources: list[ArtifactSource]
    metadata: dict[str, Any] | list[dict[str, Any]] | None = None

class JinjaMapping(Command[Any]):
    context: Any