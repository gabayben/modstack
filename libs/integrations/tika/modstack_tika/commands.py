from typing import Any

from modstack.commands import Command
from modstack.typing import ArtifactSource, TextArtifact

class TikaToText(Command[list[TextArtifact]]):
    sources: list[ArtifactSource]
    metadata: dict[str, Any] | list[dict[str, Any]] | None = None