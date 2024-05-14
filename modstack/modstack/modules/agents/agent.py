from abc import ABC

from modstack.commands import CommandHandler, CommandId, LLMCommand, Tool
from modstack.commands.base import TCommand
from modstack.modules import Module
from modstack.typing import ChatMessage
from modstack.typing.vars import Out

class Agent(Module, ABC):
    @property
    def provided_handlers(self) -> dict[CommandId, CommandHandler]:
        return self._provided_handlers

    @property
    def tools(self) -> dict[CommandId, Tool]:
        return self._tools

    def __init__(
        self,
        llm: CommandHandler[LLMCommand, list[ChatMessage]] | Module,
        tools: list[Tool] | None = None,
        **kwargs
    ):
        super().__init__()
        self._provided_handlers: dict[CommandId, CommandHandler] = {}
        self._tools: dict[CommandId, Tool] = {}
        if isinstance(llm, CommandHandler):
            self.provide_handler(llm)
        else:
            self.provide_module(llm)
        if tools:
            self.add_tools(*tools)

    def provide_handler(
        self,
        handler: CommandHandler[TCommand, Out],
        module: str | None = None
    ) -> None:
        self.provided_handlers[CommandId(handler.command, module)] = handler

    def provide_module(
        self,
        module: Module,
        name: str | None = None
    ):
        name = name or module.__class__.__name__
        for handler in module.handlers.values():
            self.provide_handler(handler, module=name)

    def add_tools(self, *tools: Tool) -> None:
        for tool in tools:
            if (tool.command, tool.module) in self.provided_handlers:
                self.tools[CommandId(tool.command, tool.module)] = tool