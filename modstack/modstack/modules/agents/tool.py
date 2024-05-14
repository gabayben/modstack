from typing import Any, NotRequired, TypedDict

from pydantic import Field

from modstack.typing import Serializable

class ToolParameter(TypedDict):
    name: str
    description: NotRequired[str | None]
    metadata: NotRequired[dict[str, Any] | None]

class Tool(Serializable):
    name: str
    description: str | None = None
    parameters: list[ToolParameter] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)