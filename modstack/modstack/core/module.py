import inspect
from typing import Any, AsyncIterator, Iterator, Type, final

from modstack.constants import COMMAND_TYPE
from modstack.containers import Effect
from modstack.core import Command, CommandHandler
from modstack.core.command import TCommand
from modstack.typing.vars import Out

class Module:
    @property
    def handlers(self) -> dict[Type[Command], CommandHandler]:
        return self._handlers

    def __init__(self, **kwargs):
        self._handlers = {
            getattr(handler, COMMAND_TYPE): CommandHandler(handler)
            for _, handler in inspect.getmembers(self, lambda x: hasattr(x, COMMAND_TYPE))
        }

    def get_handler(
        self,
        command_type: Type[TCommand],
        output_type: Type[Out] = Any
    ) -> CommandHandler[TCommand, Out]:
        return self.handlers[command_type]

    def effect(self, command: Command[Out]) -> Effect[Out]:
        return self.get_handler(type(command), type(Out)).effect(command)

    @final
    def invoke(self, command: Command[Out]) -> Out:
        return self.effect(command).invoke()

    @final
    async def ainvoke(self, command: Command[Out]) -> Out:
        return await self.effect(command).ainvoke()

    @final
    def iter(self, command: Command[Out]) -> Iterator[Out]:
        yield from self.effect(command).iter()

    @final
    async def aiter(self, command: Command[Out]) -> AsyncIterator[Out]:
        async for item in self.effect(command).aiter(): #type: ignore
            yield item