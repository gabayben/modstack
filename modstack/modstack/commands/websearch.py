from typing import Any, TypeVar

from pydantic import Field

from modstack.commands import Command
from modstack.typing import LinkArtifact, Serializable, TextArtifact

_T = TypeVar('_T')

class SearchEngineResponse(Serializable):
    links: list[LinkArtifact]
    content: list[TextArtifact] = Field(default_factory=list)

class SearchEngineQueryBase(Command[_T]):
    query: str
    allowed_domains: list[str] | None = None
    search_params: dict[str, Any] | None = None

class SearchEngineQuery(SearchEngineQueryBase[SearchEngineResponse]):
    pass