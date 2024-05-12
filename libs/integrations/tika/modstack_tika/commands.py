from typing import Any

from modstack.commands import Command
from modstack.typing import ArtifactSource, Utf8Artifact

class TikaToText(Command[list[Utf8Artifact]]):
    sources: list[ArtifactSource]
    metadata: dict[str, Any] | list[dict[str, Any]] | None = None