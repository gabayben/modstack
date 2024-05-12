from typing import Any

from modstack.commands import Command
from modstack.typing import Serializable
from modstack_serper.search import SerperKnowledgeGraph, SerperOrganicResult, SerperPeopleAlsoAsk

class SerperSearchResponse(Serializable):
    organic: list[SerperOrganicResult]
    knowledge_graph: SerperKnowledgeGraph | None = None
    people_also_ask: SerperPeopleAlsoAsk | None = None
    related_searches: list[str] | None = None

class SerperSearchQuery(Command[SerperSearchResponse]):
    query: str
    allowed_domains: list[str] | None = None
    search_params: dict[str, Any] | None = None