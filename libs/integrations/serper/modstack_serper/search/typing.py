from typing import Any, NotRequired, TypedDict

from modstack_serper.typing import SerperSiteLink

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