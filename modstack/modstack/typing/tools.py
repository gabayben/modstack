from typing import Any, NotRequired, Type, TypedDict

from pydantic import Field

from modstack.typing import Serializable

class ToolParameter(TypedDict):
    type: Type
    required: bool
    allowed_values: NotRequired[list[Any] | None]
    description: NotRequired[str | None]
    metadata: NotRequired[dict[str, Any] | None]

class Tool(Serializable):
    name: str
    description: str | None = None
    parameters: dict[str, ToolParameter] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def __init__(
        self,
        name: str,
        description: str | None = None,
        parameters: dict[str, ToolParameter] = {},
        metadata: dict[str, Any] = {},
        **kwargs
    ):
        super().__init__(
            name=name,
            description=description,
            parameters=parameters,
            metadata=metadata,
            **kwargs
        )