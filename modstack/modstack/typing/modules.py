from pydantic import Field

from modstack.artifacts import Artifact, Link
from modstack.typing import Schema

class SearchEngineResponse(Schema):
    links: list[Link]
    content: list[Artifact] = Field(default_factory=list)