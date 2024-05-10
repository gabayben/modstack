from modstack.commands import Command
from modstack.typing import ArtifactSource, StrictArtifactSource

class RouteByMimeType(Command[dict[str, list[StrictArtifactSource]]]):
    sources: list[ArtifactSource]