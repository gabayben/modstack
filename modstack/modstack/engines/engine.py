from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Iterator, Type

from modstack.contracts import Contract
from modstack.endpoints import Endpoint
from modstack.modules import Module
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
        output_type: Type[Out] = Any,
        **kwargs
    ) -> Effect[Out]:
        return self.get_endpoint(path, output_type=output_type)(*args, **kwargs)

    def effect(self, path: str, contract: Contract[Out]) -> Effect[Out]:
        return self.get_endpoint(path, type(Out)).effect(contract)

    def invoke(self, path: str, contract: Contract[Out]) -> Out:
        return self.effect(path, contract).invoke()

    async def ainvoke(self, path: str, contract: Contract[Out]) -> Out:
        return await self.effect(path, contract).ainvoke()

    def iter(self, path: str, contract: Contract[Out]) -> Iterator[Out]:
        yield from self.effect(path, contract).iter()

    async def aiter(self, path: str, contract: Contract[Out]) -> AsyncIterator[Out]:
        async for item in self.effect(path, contract).aiter():  # type: ignore
            yield item

class Engine(EngineBase):
    @property
    def modules(self) -> dict[str, Module]:
        return self._modules

    @property
    def endpoints(self) -> dict[str, Endpoint]:
        return self._endpoints

    def __init__(self, name: str):
        self.name = name
        self._modules: dict[str, Module] = {}
        self._endpoints: dict[str, Endpoint] = {}

    def as_context(self) -> 'EngineContext':
        return EngineContext(self)

    def add_module(self, name: str, module: Module):
        self.modules[name] = module

    def add_endpoint(self, endpoint: Endpoint, name: str | None = None) -> None:
        pass

    def get_endpoint(
        self,
        path: str,
        output_type: Type[Out] = Any
    ) -> Endpoint[Out]:
        return self.endpoints[path]

class EngineContext(EngineBase):
    def __init__(self, engine: Engine):
        self._engine = engine

    def get_endpoint(
        self,
        path: str,
        output_type: Type[Out] = Any
    ) -> Endpoint[Out]:
        return self._engine.get_endpoint(path, output_type=output_type)