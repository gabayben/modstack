from abc import ABC
from typing import Any, TypeVar

from pydantic import Field

from modstack.commands import Command
from modstack.typing import LinkArtifact, Serializable, Utf8Artifact

_T = TypeVar('_T')

class SearchEngineResponse(Serializable):
    links: list[LinkArtifact]
    content: list[Utf8Artifact] = Field(default_factory=list)

class SearchEngineQueryBase(Command[_T], ABC):
    query: str
    allowed_domains: list[str] | None = None
    search_params: dict[str, Any] | None = None

class SearchEngineQuery(SearchEngineQueryBase[SearchEngineResponse]):
    @classmethod
    def name(cls) -> str:
        return 'search_engine_query'