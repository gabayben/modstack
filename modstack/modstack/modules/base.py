import inspect
from typing import Any, Type

from pydantic import BaseModel

from modstack.commands import Command, CommandHandler, CommandNotFound
from modstack.commands.base import TCommand
from modstack.constants import MODSTACK_COMMAND
from modstack.typing.vars import Out

class Module:
    @property
    def handlers(self) -> dict[Type[Command], CommandHandler]:
        return self._handlers

    def __init__(self, **kwargs):
        self._handlers: dict[Type[Command], CommandHandler] = {}
        for _, func in inspect.getmembers(self, lambda x: callable(x) and hasattr(x, MODSTACK_COMMAND)):
            self.add_handler(CommandHandler(func))

    def get_handler(self, command: Type[TCommand], output_type: Type[Out] = Any) -> CommandHandler[TCommand, Out]:
        if command not in self.handlers:
            raise CommandNotFound(f'Command {command.name()} not found in Module {self.__class__.__name__}')
        return self.handlers[command]

    def add_handler(self, handler: CommandHandler[TCommand, Out]) -> None:
        self.handlers[handler.command] = handler

    def get_input_schema(self, command: Type[TCommand]) -> Type[BaseModel]:
        return self.get_handler(command).input_schema

    def set_input_schema(self, command: Type[TCommand], input_schema: Type[BaseModel]) -> None:
        handler = self.get_handler(command)
        setattr(handler, 'input_schema', input_schema)

    def get_output_schema(self, command: Type[TCommand]) -> Type[BaseModel]:
        return self.get_handler(command).output_schema

    def set_output_schema(self, command: Type[TCommand], output_schema: Type[BaseModel]) -> None:
        handler = self.get_handler(command)
        setattr(handler, 'output_schema', output_schema)