from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Iterator, Type

from modstack.contracts import Contract
from modstack.endpoints import Endpoint
from modstack.typing import Effect
from modstack.typing.vars import Out

class EngineBase(ABC):
    @abstractmethod
    def get_endpoint(self, path: str, output_type: Type[Out] = Any) -> Endpoint[Out]:
        pass

    def call(
        self,
        path: str,
        *args,
        __output_type__: Type[Out] = Any,
        **kwargs
    ) -> Effect[Out]:
        return self.get_endpoint(path, output_type=__output_type__)(*args, **kwargs)

    def effect(self, path: str, contract: Contract[Out]) -> Effect[Out]:
        return self.get_endpoint(path, type(Out)).effect(contract)

    def invoke(self, path: str, contract: Contract[Out]) -> Out:
        return self.effect(path, contract).invoke()

    async def ainvoke(self, path: str, contract: Contract[Out]) -> Out:
        return await self.effect(path, contract).ainvoke()

    def iter(self, path: str, contract: Contract[Out]) -> Iterator[Out]:
        yield from self.effect(path, contract).iter()

    async def aiter(self, path: str, contract: Contract[Out]) -> AsyncIterator[Out]:
        async for item in self.effect(path, contract).aiter(): # type: ignore
            yield item