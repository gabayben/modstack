from typing import Any, TypeVar

from modstack.commands import Command
from modstack.typing import ReferenceArtifact

_T = TypeVar('_T')

class SearchEngineQueryBase(Command[_T]):
    query: str
    allowed_domains: list[str] | None = None
    search_params: dict[str, Any] | None = None

class SearchEngineQuery(SearchEngineQueryBase[list[ReferenceArtifact]]):
    pass