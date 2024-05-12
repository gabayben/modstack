from modstack.commands.websearch import SearchEngineQueryBase
from modstack.typing import Serializable
from modstack_serper.search import SerperKnowledgeGraph, SerperOrganicResult, SerperPeopleAlsoAsk

class SerperSearchResponse(Serializable):
    organic: list[SerperOrganicResult]
    knowledge_graph: SerperKnowledgeGraph | None = None
    people_also_ask: list[SerperPeopleAlsoAsk] | None = None
    related_searches: list[str] | None = None

class SerperSearchQuery(SearchEngineQueryBase[SerperSearchResponse]):
    country: str | None = None
    language: str | None = None
    autocomplete: bool | None = None