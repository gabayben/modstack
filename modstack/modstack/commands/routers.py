from modstack.commands import Command
from modstack.typing import Artifact, ArtifactSource, StrictArtifactSource, TextArtifact

class RouteArtifacts(Command[dict[str, list[Artifact]]]):
    artifacts: list[Artifact]

class RouteByMimeType(Command[dict[str, list[StrictArtifactSource]]]):
    sources: list[ArtifactSource]

class RouteByLanguage(Command[dict[str, list[TextArtifact]]]):
    artifacts: list[TextArtifact]