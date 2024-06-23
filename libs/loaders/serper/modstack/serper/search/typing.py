from typing import Any, NotRequired, TypedDict

from modstack.serper.typing import SerperSiteLink
from modstack.typing import Schema

class SerperOrganicResult(TypedDict):
    title: str
    link: str
    snippet: str
    position: int
    date: NotRequired[str | None]
    image_url: NotRequired[str | None]
    site_links: NotRequired[list[SerperSiteLink] | None]
    attributes: NotRequired[dict[str, Any] | None]

class SerperKnowledgeGraph(TypedDict):
    title: str
    type: str
    website: str
    description: str
    description_source: str
    description_link: NotRequired[str | None]
    image_url: NotRequired[str | None]
    attributes: NotRequired[dict[str, Any] | None]

class SerperPeopleAlsoAsk(TypedDict):
    question: str
    title: str
    snippet: str
    link: str

class SerperError(Exception):
    pass

class SerperSearchResponse(Schema):
    organic: list[SerperOrganicResult]
    knowledge_graph: SerperKnowledgeGraph | None = None
    people_also_ask: list[SerperPeopleAlsoAsk] | None = None
    related_searches: list[str] | None = None