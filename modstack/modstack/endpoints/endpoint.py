import inspect
from inspect import Parameter
from types import MappingProxyType
from typing import Any, AsyncIterator, Callable, Generic, Iterator, Type, get_args

from modstack.contracts import Contract
from modstack.typing import CallableType, Effect, Effects
from pydantic import BaseModel

from modstack.constants import IGNORE_INPUT_SCHEMA, IGNORE_OUTPUT_SCHEMA, MODSTACK_ENDPOINT
from modstack.typing.vars import Out
from modstack.utils.serialization import create_model, create_schema, from_parameters

class EndpointNotFound(Exception):
    pass

class AmbiguousEndpoints(Exception):
    pass

class Endpoint(Generic[Out]):
    _call: Callable[..., Effect[Out]]
    callable_type: CallableType
    name: str
    parameters: MappingProxyType[str, Parameter]
    return_annotation: Any
    input_schema: Type[BaseModel]
    output_schema: Type[BaseModel]

    def __init__(self, func: Callable[..., Out]):
        if inspect.isasyncgenfunction(func):
            self.callable_type = 'aiter'
        elif inspect.isgeneratorfunction(func):
            self.callable_type = 'iter'
        elif inspect.iscoroutinefunction(func):
            self.callable_type = 'ainvoke'
        else:
            self.callable_type = 'invoke'

        def fn(*args, **kwargs) -> Effect[Out]:
            if self.callable_type == 'aiter':
                async def _fn() -> AsyncIterator[Out]:
                    async for item in func(*args, **kwargs):
                        yield item

                return Effects.AsyncIterator(_fn)
            elif self.callable_type == 'iter':
                def _fn() -> Iterator[Out]:
                    yield from func(*args, **kwargs)

                return Effects.Iterator(_fn)
            elif self.callable_type == 'ainvoke':
                async def _fn() -> Out:
                    return await func(*args, **kwargs)

                return Effects.Async(_fn)
            else:
                def _fn() -> Out:
                    return func(*args, **kwargs)

                return Effects.Sync(_fn)

        self._call = fn
        self.name = getattr(func, 'name', None) or func.__name__
        signature = inspect.signature(func)
        self.parameters = signature.parameters
        self.return_annotation = self._get_return_annotation(signature.return_annotation)

        if not getattr(self, IGNORE_INPUT_SCHEMA, False):
            self.input_schema = create_model(
                f'{self.name}Input',
                **from_parameters(self.parameters)
            )
        if not getattr(self, IGNORE_OUTPUT_SCHEMA, False):
            self.output_schema = create_schema(f'{self.name}Output', self.return_annotation)

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

    def _get_return_annotation(self, annotation: Any) -> Any:
        if self.callable_type == 'iter' or self.callable_type == 'aiter':
            return get_args(annotation)[0]
        return annotation

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