import inspect
from typing import Any, Type

from pydantic import BaseModel

from modstack.constants import COMMAND_TYPE
from modstack.commands import Command, CommandHandler
from modstack.commands.base import TCommand
from modstack.typing.vars import Out

class Module:
    @property
    def handlers(self) -> dict[Type[Command], CommandHandler]:
        return self._handlers

    def __init__(self, **kwargs):
        self._handlers = {
            getattr(handler, COMMAND_TYPE): CommandHandler(handler)
            for _, handler in inspect.getmembers(self, lambda x: callable(x) and hasattr(x, COMMAND_TYPE))
        }

    def get_handler(
        self,
        command_type: Type[TCommand],
        output_type: Type[Out] = Any
    ) -> CommandHandler[TCommand, Out]:
        return self.handlers[command_type]

    def set_output_schema(
        self,
        command_type: Type[TCommand],
        output_schema: Type[BaseModel]
    ) -> None:
        handler = self.get_handler(command_type)
        setattr(handler, 'output_schema', output_schema)