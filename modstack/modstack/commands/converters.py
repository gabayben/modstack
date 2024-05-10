from typing import Any

from modstack.commands import Command
from modstack.typing import ArtifactSource, TextArtifact

class ToText(Command[list[TextArtifact]]):
    sources: list[ArtifactSource]
    metadata: dict[str, Any] | list[dict[str, Any]] | None = None

class MarkdownToText(Command[list[TextArtifact]]):
    sources: list[ArtifactSource]
    metadata: dict[str, Any] | list[dict[str, Any]] | None = None

class HtmlToText(Command[list[TextArtifact]]):
    sources: list[ArtifactSource]
    metadata: dict[str, Any] | list[dict[str, Any]] | None = None

class PDFToText(Command[list[TextArtifact]]):
    sources: list[ArtifactSource]
    metadata: dict[str, Any] | list[dict[str, Any]] | None = None

class JinjaMapping(Command[Any]):
    context: Any