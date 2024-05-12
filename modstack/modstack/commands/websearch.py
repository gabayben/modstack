from typing import Any

from modstack.commands import Command
from modstack.typing import Artifact, Serializable

class SearchEngineResponse(Serializable):
    artifacts: list[Artifact]
    links: list[str]

class SearchEngineQuery(Command[SearchEngineResponse]):
    query: str
    allowed_domains: list[str] | None = None
    search_params: dict[str, Any] | None = None