from abc import ABC
from typing import Any, Type

from modstack.core import Command, CommandHandler, Module
from modstack.core.command import TCommand
from modstack.typing.vars import Out

class Structure(ABC):
    _handlers: dict[Type[Command], CommandHandler]
    _modules: list[Module]

    @property
    def handlers(self) -> dict[Type[Command], CommandHandler]:
        return self._handlers

    @property
    def modules(self) -> list[Module]:
        return self._modules

    def __init__(self):
        self._handlers = {}
        self._modules = []

    def get_handler(
        self,
        command_type: Type[TCommand],
        output_type: Type[Out] = Any
    ) -> CommandHandler[TCommand, Out]:
        return self.handlers[command_type]

    def add_handler(
        self,
        command_type: Type[TCommand],
        handler: CommandHandler[TCommand, Out]
    ) -> None:
        self.handlers[command_type] = handler

    def add_module(self, module: Module) -> None:
        self.modules.append(module)
        for command_type, handler in module.handlers.items():
            self.add_handler(command_type, handler)