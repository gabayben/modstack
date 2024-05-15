import inspect
from inspect import Parameter
from types import MappingProxyType
from typing import Any, AsyncIterator, Callable, Generic, Iterator, Type

from modstack.contracts import Contract
from modstack.typing import Effect, Effects
from pydantic import BaseModel

from modstack.constants import IGNORE_INPUT_SCHEMA, IGNORE_OUTPUT_SCHEMA, MODSTACK_ENDPOINT
from modstack.typing.vars import Out

class EndpointNotFound(Exception):
    pass

class AmbiguousEndpoints(Exception):
    pass

class Endpoint(Generic[Out]):
    _call: Callable[..., Effect[Out]]
    name: str
    parameters: MappingProxyType[str, Parameter]
    return_annotation: Any
    input_schema: Type[BaseModel]
    output_schema: Type[BaseModel]

    def __init__(self, func: Callable[..., Out]):
        def fn(*args, **kwargs) -> Effect[Out]:
            if inspect.isasyncgenfunction(func):
                async def _fn() -> AsyncIterator[Out]:
                    async for item in func(*args, **kwargs):
                        yield item

                return Effects.AsyncIterator(_fn)
            elif inspect.isabstract(func):
                def _fn() -> Iterator[Out]:
                    yield from func(*args, **kwargs)

                return Effects.Iterator(_fn)
            elif inspect.iscoroutinefunction(func):
                async def _fn() -> Out:
                    return await func(*args, **kwargs)

                return Effects.Async(_fn)
            else:
                def _fn() -> Out:
                    return func(*args, **kwargs)

                return Effects.Sync(_fn)

        self._call = fn
        signature = inspect.signature(func)
        self.name = getattr(func, 'name', None) or func.__name__
        self.parameters = signature.parameters
        self.return_annotation = signature.return_annotation

        if not getattr(self, IGNORE_INPUT_SCHEMA, False):
            pass
        if not getattr(self, IGNORE_OUTPUT_SCHEMA, False):
            pass

    def __call__(self, *args, **kwargs) -> Effect[Out]:
        return self._call(*args, **kwargs)

    def effect(self, contract: Contract[Out]) -> Effect[Out]:
        return self(**dict(contract))

    def invoke(self, contract: Contract[Out]) -> Out:
        return self.effect(contract).invoke()

    async def ainvoke(self, contract: Contract[Out]) -> Out:
        return await self.effect(contract).ainvoke()

    def iter(self, contract: Contract[Out]) -> Iterator[Out]:
        yield from self.effect(contract).iter()

    async def aiter(self, contract: Contract[Out]) -> AsyncIterator[Out]:
        async for item in self.effect(contract).ainvoke(): #type: ignore
            yield item

def endpoint[Out](
    func: Callable[..., Out] | None = None,
    name: str | None = None,
    ignore_input_schema: bool = False,
    ignore_output_schema: bool = False
) -> Callable[..., Out]:
    def wrapper(fn: Callable[..., Out]) -> Callable[..., Out]:
        setattr(fn, MODSTACK_ENDPOINT, True)
        setattr(fn, 'name', name or fn.__name__)
        setattr(fn, IGNORE_INPUT_SCHEMA, ignore_input_schema)
        setattr(fn, IGNORE_OUTPUT_SCHEMA, ignore_output_schema)
        return fn

    return wrapper(func) if func else wrapper

def minimal_endpoint[Out](
    func: Callable[..., Out] | None = None,
    name: str | None = None
) -> Endpoint[Out]:
    def wrapper(fn: Callable[..., Out]) -> Endpoint[Out]:
        setattr(fn, MODSTACK_ENDPOINT, True)
        setattr(fn, 'name', name or fn.__name__)
        return Endpoint(fn)

    return wrapper(func) if func else wrapper