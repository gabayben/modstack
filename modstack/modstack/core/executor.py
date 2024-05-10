from typing import AsyncIterator, Iterator, final

from modstack.containers import Effect
from modstack.core import Command, Structure
from modstack.typing.vars import Out

@final
class Executor(Structure):
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