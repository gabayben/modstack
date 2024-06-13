from pydantic import Field

from modstack.artifacts import LinkArtifact, Utf8Artifact
from modstack.typing import Schema

class SearchEngineResponse(Schema):
    links: list[LinkArtifact]
    content: list[Utf8Artifact] = Field(default_factory=list)