from modstack.commands import Command
from modstack.typing import Artifact, ArtifactSource, StrictArtifactSource, Utf8Artifact

class RouteArtifacts(Command[dict[str, list[Artifact]]]):
    artifacts: list[Artifact]

    @classmethod
    def name(cls) -> str:
        return 'route_artifacts'

class RouteByMimeType(Command[dict[str, list[StrictArtifactSource]]]):
    sources: list[ArtifactSource]

    @classmethod
    def name(cls) -> str:
        return 'route_by_mime_type'

class RouteByLanguage(Command[dict[str, list[Utf8Artifact]]]):
    artifacts: list[Utf8Artifact]

    @classmethod
    def name(cls) -> str:
        return 'route_by_language'