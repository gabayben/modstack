from typing import Any, Iterable, NotRequired, Type, TypedDict

from pydantic import Field

from modstack.contracts import Contract
from modstack.typing import ChatMessage, Serializable

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

class LLMCall(Contract[Iterable[ChatMessage]]):
    messages: Iterable[ChatMessage]
    tools: list[Tool] | None = None
    generation_args: dict[str, Any] | None = None

    def __init__(
        self,
        messages: list[ChatMessage],
        tools: list[Tool] | None = None,
        generation_args: dict[str, Any] | None = None,
        **kwargs
    ):
        super().__init__(
            messages=messages,
            tools=tools,
            generation_args=generation_args,
            **kwargs
        )

    @classmethod
    def name(cls) -> str:
        return 'llm_call'