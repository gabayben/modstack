from modstack.contracts import Contract
from modstack.typing import Artifact, ArtifactSource, StrictArtifactSource, Utf8Artifact

class RouteArtifacts(Contract[dict[str, list[Artifact]]]):
    artifacts: list[Artifact]

    @classmethod
    def name(cls) -> str:
        return 'route_artifacts'

class RouteByMimeType(Contract[dict[str, list[StrictArtifactSource]]]):
    sources: list[ArtifactSource]

    @classmethod
    def name(cls) -> str:
        return 'route_by_mime_type'

class RouteByLanguage(Contract[dict[str, list[Utf8Artifact]]]):
    artifacts: list[Utf8Artifact]

    @classmethod
    def name(cls) -> str:
        return 'route_by_language'