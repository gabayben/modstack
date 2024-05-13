import inspect
from inspect import Parameter
from types import MappingProxyType
from typing import Any, AsyncIterator, Callable, Generic, Iterator, Type, TypeVar

from pydantic import BaseModel
from typing_extensions import ParamSpec

from modstack.containers import Effect, Effects

P = ParamSpec('P')
Out = TypeVar('Out')

class Plugin(Generic[Out, P]):
    call: Callable[P, Effect[Out]]
    parameters: MappingProxyType[str, Parameter]
    return_annotation: Any
    input_schema: Type[BaseModel]
    output_schema: Type[BaseModel]

    def __init__(self, func: Callable[P, Out]):
        def fn(*args: P.args, **kwargs: P.kwargs) -> Effect[Out]:
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

        self.call = fn
        signature = inspect.signature(func)
        self.parameters = signature.parameters
        self.return_annotation = signature.return_annotation