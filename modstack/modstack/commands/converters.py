from typing import Any, Type

from pydantic import Field

from modstack.commands import Command
from modstack.typing import ArtifactSource, TextArtifact
from modstack.typing.vars import Out

class FromTextFile(Command[list[TextArtifact]]):
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

class JinjaMapping(Command[Out]):
    context: Any

    def __init__(self, output_type: Type[Out], **data):
        super().__init__(**data)
        self.output_type = Field(default=output_type, exclude=True)