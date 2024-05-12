from typing import AsyncIterator, Iterator, final

from modstack.containers import Effect
from modstack.commands import Command
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

    def add_module(self, module: Module) -> None:
        if module not in self.modules:
            self.modules.append(module)
            for handlers in module.commands.values():
                for handler in handlers.values():
                    self.add_handler(handler)

    def effect(self, command: Command[Out], name: str | None = None) -> Effect[Out]:
        return self.get_handler(
            type(command),
            name=name,
            output_type=type(Out)
        ).effect(command)

    def invoke(self, command: Command[Out], name: str | None = None) -> Out:
        return self.effect(command, name=name).invoke()

    async def ainvoke(self, command: Command[Out], name: str | None = None) -> Out:
        return await self.effect(command, name=name).ainvoke()

    def iter(self, command: Command[Out], name: str | None = None) -> Iterator[Out]:
        yield from self.effect(command, name=name).iter()

    async def aiter(self, command: Command[Out], name: str | None = None) -> AsyncIterator[Out]:
        async for item in self.effect(command, name=name).aiter(): # type: ignore
            yield item