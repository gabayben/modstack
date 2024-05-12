from typing import Any, TypeVar

from modstack.commands import Command
from modstack.typing import Artifact, Serializable

_T = TypeVar('_T')

class SearchEngineResponse(Serializable):
    artifacts: list[Artifact]
    links: list[str]

class SearchEngineQueryBase(Command[_T]):
    query: str
    allowed_domains: list[str] | None = None
    search_params: dict[str, Any] | None = None

class SearchEngineQuery(SearchEngineQueryBase[SearchEngineResponse]):
    pass