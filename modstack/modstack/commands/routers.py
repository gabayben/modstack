from modstack.commands import Command
from modstack.typing import Artifact, ArtifactSource, StrictArtifactSource, Utf8Artifact

class RouteArtifacts(Command[dict[str, list[Artifact]]]):
    artifacts: list[Artifact]

class RouteByMimeType(Command[dict[str, list[StrictArtifactSource]]]):
    sources: list[ArtifactSource]

class RouteByLanguage(Command[dict[str, list[Utf8Artifact]]]):
    artifacts: list[Utf8Artifact]