from typing import Any, AsyncIterator, Iterator, Type

from modstack.contracts import Contract
from modstack.endpoints import Endpoint
from modstack.modules import Module
from modstack.typing import Effect
from modstack.typing.vars import Out

class Engine:
    @property
    def endpoints(self) -> dict[str, Endpoint]:
        return self._endpoints

    def __init__(self, name: str):
        self.name = name
        self._endpoints: dict[str, Endpoint] = {}

    def add_module(self, name: str, module: Module):
        pass

    def add_endpoint(self, endpoint: Endpoint, name: str | None = None) -> None:
        pass

    def get_endpoint(self, path: str, output_type: Type[Out] = Any) -> Endpoint[Out]:
        return self.endpoints[path]

    def effect(self, path: str, contract: Contract[Out]) -> Effect[Out]:
        return self.get_endpoint(path, type(Out)).effect(contract)

    def invoke(self, path: str, contract: Contract[Out]) -> Out:
        return self.effect(path, contract).invoke()

    async def ainvoke(self, path: str, contract: Contract[Out]) -> Out:
        return await self.effect(path, contract).ainvoke()

    def iter(self, path: str, contract: Contract[Out]) -> Iterator[Out]:
        yield from self.effect(path, contract).iter()

    async def aiter(self, path: str, contract: Contract[Out]) -> AsyncIterator[Out]:
        async for item in self.effect(path, contract).aiter(): #type: ignore
            yield item