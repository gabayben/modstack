from modstack.commands.websearch import SearchEngineQueryBase
from modstack.typing import Serializable
from modstack_serper.search import SerperKnowledgeGraph, SerperOrganicResult, SerperPeopleAlsoAsk

class SerperSearchResponse(Serializable):
    organic: list[SerperOrganicResult]
    knowledge_graph: SerperKnowledgeGraph | None = None
    people_also_ask: SerperPeopleAlsoAsk | None = None
    related_searches: list[str] | None = None

class SerperSearchQuery(SearchEngineQueryBase[SerperSearchResponse]):
    pass