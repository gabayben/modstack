import inspect
from inspect import Parameter
from types import MappingProxyType
from typing import Any, AsyncIterator, Callable, Generic, Iterator, Type

from pydantic import BaseModel
from typing_extensions import ParamSpec

from modstack.constants import IGNORE_INPUT_SCHEMA, IGNORE_OUTPUT_SCHEMA, MODSTACK_FEATURE
from modstack.containers import Effect, Effects
from modstack.typing.vars import Out

P = ParamSpec('P')

class FeatureNotFound(Exception):
    pass

class AmbiguousFeatures(Exception):
    pass

class Feature(Generic[Out, P]):
    _call: Callable[P, Effect[Out]]
    name: str
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

        self._call = fn
        signature = inspect.signature(func)
        self.name = getattr(func, 'name', None) or func.__name__
        self.parameters = signature.parameters
        self.return_annotation = signature.return_annotation

        if not getattr(self, IGNORE_INPUT_SCHEMA, False):
            pass
        if not getattr(self, IGNORE_OUTPUT_SCHEMA, False):
            pass

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> Effect[Out]:
        return self._call(*args, **kwargs)

def feature[Out, **P](
    func: Callable[P, Out] | None = None,
    name: str | None = None,
    ignore_input_schema: bool = False,
    ignore_output_schema: bool = False
) -> Callable[P, Out]:
    def wrapper(fn: Callable[P, Out]) -> Callable[P, Out]:
        setattr(fn, MODSTACK_FEATURE, True)
        setattr(fn, 'name', name or fn.__name__)
        setattr(fn, IGNORE_INPUT_SCHEMA, ignore_input_schema)
        setattr(fn, IGNORE_OUTPUT_SCHEMA, ignore_output_schema)
        return fn
    return wrapper(func) if func else wrapper

def feature_fn[Out, **P](
    func: Callable[P, Out] | None = None,
    name: str | None = None
) -> Feature[Out, P]:
    def wrapper(fn: Callable[P, Out]) -> Feature[Out, P]:
        setattr(fn, MODSTACK_FEATURE, True)
        setattr(fn, 'name', name or fn.__name__)
        return Feature(fn)
    return wrapper(func) if func else wrapper