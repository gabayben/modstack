from typing import Any, NotRequired, Type, TypedDict

from pydantic import Field

from modstack.commands import Command
from modstack.typing import ChatMessage, Serializable

class ToolParameter(TypedDict):
    type: str
    description: str
    required: bool
    allowed_values: NotRequired[list[Any] | None]
    metadata: NotRequired[dict[str, Any] | None]

class Tool(Serializable):
    command: Type[Command]
    description: str
    module: str | None = None
    parameters: dict[str, ToolParameter] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def __init__(
        self,
        command: Type[Command],
        description: str,
        module: str | None = None,
        parameters: dict[str, ToolParameter] = {},
        metadata: dict[str, Any] = {},
        **kwargs
    ):
        super().__init__(
            command=command,
            description=description,
            module=module,
            parameters=parameters,
            metadata=metadata,
            **kwargs
        )

class LLMCommand(Command[list[ChatMessage]]):
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