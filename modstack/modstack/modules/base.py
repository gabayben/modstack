from collections import defaultdict
import inspect
from typing import Any, Type

from pydantic import BaseModel

from modstack.constants import COMMAND_TYPE
from modstack.commands import Command, CommandHandler
from modstack.commands.base import TCommand
from modstack.typing.vars import Out

class Module:
    @property
    def commands(self) -> dict[Type[Command], dict[str, CommandHandler]]:
        return self._commands

    def __init__(self, **kwargs):
        self._commands: dict[Type[Command], dict[str, CommandHandler]] = defaultdict(dict)
        for _, func in inspect.getmembers(self, lambda x: callable(x) and hasattr(x, COMMAND_TYPE)):
            self.add_handler(CommandHandler(func))

    def get_handler(
        self,
        command_type: Type[TCommand],
        name: str | None = None,
        output_type: Type[Out] = Any
    ) -> CommandHandler[TCommand, Out]:
        return (
            self.commands[command_type][name] if name
            else list(self.commands[command_type].values())[0]
        )

    def add_handler(self, handler: CommandHandler[TCommand, Out]) -> None:
        self.commands[handler.command_type][handler.name] = handler

    def get_input_schema(self, command_type: Type[TCommand], name: str | None = None) -> Type[BaseModel]:
        return self.get_handler(command_type, name=name).input_schema

    def get_output_schema(self, command_type: Type[TCommand], name: str | None = None) -> Type[BaseModel]:
        return self.get_handler(command_type, name=name).output_schema

    def set_input_schema(
        self,
        command_type: Type[TCommand],
        input_schema: Type[BaseModel],
        name: str | None = None
    ) -> None:
        handler = self.get_handler(command_type, name=name)
        setattr(handler, 'input_schema', input_schema)

    def set_output_schema(
        self,
        command_type: Type[TCommand],
        output_schema: Type[BaseModel],
        name: str | None = None
    ) -> None:
        handler = self.get_handler(command_type, name=name)
        setattr(handler, 'output_schema', output_schema)