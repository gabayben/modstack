from typing import Any, NotRequired, TypedDict

class SerperSiteLink(TypedDict):
    title: str
    link: str

class SerperOrganicResult(TypedDict):
    title: str
    link: str
    snippet: str
    position: int
    site_links: NotRequired[list[SerperSiteLink] | None]

class SerperKnowledgeGraph(TypedDict):
    title: str
    type: str
    website: str
    image_url: NotRequired[str | None]
    description: str
    description_source: str
    description_link: NotRequired[str | None]
    attributes: NotRequired[dict[str, Any] | None]

class SerperPeopleAlsoAsk(TypedDict):
    question: str
    title: str
    snippet: str
    link: str

class SerperError(Exception):
    pass