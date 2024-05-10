from typing import AsyncIterator, Iterator, Type, final

from modstack.containers import Effect
from modstack.commands import Command, CommandHandler
from modstack.commands.base import TCommand
from modstack.modules import Module
from modstack.typing.vars import Out

@final
class Executor(Module):
    _modules: list[Module]

    @property
    def modules(self) -> list[Module]:
        return self._modules

    def __init__(self):
        super().__init__()
        self._modules = []

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

    def effect(self, command: Command[Out]) -> Effect[Out]:
        return self.get_handler(type(command), type(Out)).effect(command)

    def invoke(self, command: Command[Out]) -> Out:
        return self.effect(command).invoke()

    async def ainvoke(self, command: Command[Out]) -> Out:
        return await self.effect(command).ainvoke()

    def iter(self, command: Command[Out]) -> Iterator[Out]:
        yield from self.effect(command).iter()

    async def aiter(self, command: Command[Out]) -> AsyncIterator[Out]:
        async for item in self.effect(command).aiter(): # type: ignore
            yield item