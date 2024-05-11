from modstack.commands import Command
from modstack.typing import Artifact, ArtifactSource, StrictArtifactSource

class RouteArtifacts(Command[dict[str, list[Artifact]]]):
    artifacts: list[Artifact]

class RouteByMimeType(Command[dict[str, list[StrictArtifactSource]]]):
    sources: list[ArtifactSource]