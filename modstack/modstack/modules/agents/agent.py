from typing import Iterator, NamedTuple, Type

from modstack.commands import Command, CommandHandler, LLMCommand, Tool
from modstack.commands.base import TCommand
from modstack.modules import Module
from modstack.typing import ChatMessage
from modstack.typing.vars import Out

class ToolId(NamedTuple):
    command: Type[Command]
    module: str | None = None

class Agent(Module):
    @property
    def modules(self) -> list[Module]:
        pass

    @property
    def provided_handlers(self) -> dict[str, CommandHandler]:
        pass

    def __init__(
        self,
        llm: CommandHandler[LLMCommand, Iterator[ChatMessage]] | Module,
        tools: list[Tool] | None = None,
        **kwargs
    ):
        super().__init__()
        if isinstance(llm, CommandHandler):
            self.provide_handler(llm)
        else:
            self.provide_module(llm)
        if tools:
            self.add_tools(*tools)

    def provide_handler(
        self,
        handler: CommandHandler[TCommand, Out],
        name: str | None = None
    ) -> None:
        pass

    def provide_module(
        self,
        module: Module,
        name: str | None = None
    ):
        pass

    def add_tools(self, *tools: Tool) -> None:
        pass