from modstack.contracts import Contract
from modstack.typing import Artifact, ArtifactSource, Utf8Artifact

class RouteArtifacts(Contract):
    artifacts: list[Artifact]

class RouteByMimeType(Contract):
    sources: list[ArtifactSource]

class RouteByLanguage(Contract):
    artifacts: list[Utf8Artifact]