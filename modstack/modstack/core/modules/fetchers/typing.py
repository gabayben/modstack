from typing import Any, TypeVar

from pydantic import Field

from modstack.core.artifacts import LinkArtifact, Utf8Artifact
from modstack.core.typing import Serializable

_T = TypeVar('_T')

class SearchEngineQuery(Serializable):
    query: str
    allowed_domains: list[str] | None = None
    search_params: dict[str, Any] | None = None

class SearchEngineResponse(Serializable):
    links: list[LinkArtifact]
    content: list[Utf8Artifact] = Field(default_factory=list)