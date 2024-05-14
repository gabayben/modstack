from typing import Any, Iterator, NotRequired, TypedDict, override

from pydantic import Field

from modstack.commands import Command
from modstack.typing import ChatMessage, Serializable

class ToolParameter(TypedDict):
    name: str
    description: NotRequired[str | None]
    metadata: NotRequired[dict[str, Any] | None]

class Tool(Serializable):
    name: str
    description: str | None = None
    parameters: list[ToolParameter] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def __init__(
        self,
        name: str,
        description: str | None = None,
        parameters: list[ToolParameter] = [],
        metadata: dict[str, Any] = Field(default_factory=dict),
        **kwargs
    ):
        super().__init__(
            name=name,
            description=description,
            parameters=parameters,
            metadata=metadata,
            **kwargs
        )

class LLMCommand(Command[Iterator[ChatMessage]]):
    messages: list[ChatMessage]
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
        return 'llm_command'