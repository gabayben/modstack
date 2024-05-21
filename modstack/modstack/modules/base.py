from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Callable, Generic, Iterator, Sequence, TYPE_CHECKING, Type, final, get_args

from pydantic import BaseModel

from modstack.typing import AfterRetryFailure, Effect, Effects, RetryStrategy, ReturnType, StopStrategy, WaitStrategy
from modstack.typing.vars import In, Out, Other
from modstack.utils.serialization import create_schema

if TYPE_CHECKING:
    from modstack.graphs.base import Graph, AsGraph
else:
    Graph = Any
    AsGraph = Any

class Module(Generic[In, Out], AsGraph, ABC):
    name: str | None = None

    @property
    def InputType(self) -> Type[In]:
        for cls in self.__class__.__orig_bases__: # type: ignore[attr-defined]
            type_args = get_args(cls)
            if type_args and len(type_args) == 1:
                return type_args[0]
        raise TypeError(
            f"Module {self.get_name()} doesn't have an inferrable InputType."
            'Override the OutputType property to specify the output type.'
        )

    @property
    def OutputType(self) -> Type[Out]:
        for cls in self.__class__.__orig_bases__: # type: ignore[attr-defined]
            type_args = get_args(cls)
            if type_args and len(type_args) == 2:
                return type_args[1]
        raise TypeError(
            f"Module {self.get_name()} doesn't have an inferrable OutputType."
            'Override the OutputType property to specify the output type.'
        )

    def __or__(self, other: 'ModuleLike[Out, Other]') -> 'Module[In, Other]':
        pass

    def __ror__(self, other: 'ModuleLike[Other, In]') -> 'Module[Other, Out]':
        pass

    def map(self, mapper: Callable[[Out], Other]) -> 'Module[In, Other]':
        pass

    def bind(self, **kwargs) -> 'Module[In, Out]':
        from modstack.modules.decorator import Decorator
        return Decorator(bound=self, kwargs=kwargs)

    def with_types(
        self,
        custom_input_type: Type[In] | BaseModel | None = None,
        custom_output_type: Type[Out] | BaseModel | None = None
    ) -> 'Module[In, Out]':
        from modstack.modules.decorator import Decorator
        return Decorator(
            bound=self,
            custom_input_type=custom_input_type,
            custom_output_type=custom_output_type
        )

    def with_retry(
        self,
        retry: RetryStrategy | None = None,
        stop: StopStrategy | None = None,
        wait: WaitStrategy | None = None,
        after: AfterRetryFailure | None = None
    ) -> 'Module[In, Out]':
        from modstack.modules.fault_handling.retry import Retry
        return Retry(
            bound=self,
            retry=retry,
            stop=stop,
            wait=wait,
            after=after
        )

    def with_fallbacks(
        self,
        fallbacks: Sequence['Module[In, Out]'],
        exceptions_to_handle: tuple[BaseException, ...] | None = None
    ) -> 'Module[In, Out]':
        from modstack.modules.fault_handling.fallbacks import Fallbacks
        return Fallbacks(
            bound=self,
            fallbacks=fallbacks,
            exceptions_to_handle=exceptions_to_handle
        )

    @abstractmethod
    def forward(self, data: In, **kwargs) -> Effect[Out]:
        pass

    @final
    def invoke(self, data: In, **kwargs) -> Out:
        return self.forward(data, **kwargs).invoke()

    @final
    async def ainvoke(self, data: In, **kwargs) -> Out:
        return await self.forward(data, **kwargs).ainvoke()

    @final
    def iter(self, data: In, **kwargs) -> Iterator[Out]:
        yield from self.forward(data, **kwargs).iter()

    @final
    async def aiter(self, data: In, **kwargs) -> AsyncIterator[Out]:
        async for item in self.effect(data, **kwargs).aiter(): #type: ignore
            yield item

    def get_name(
        self,
        name: str | None = None,
        suffix: str | None = None
    ) -> str:
        name = name or self.name or self.__class__.__name__
        if suffix:
            if name[0].isupper():
                return name + suffix.title()
            else:
                return name + '_' + suffix.lower()
        else:
            return name

    def input_schema(self) -> Type[BaseModel]:
        return create_schema(self.get_name(suffix='Input'), self.InputType)

    def output_schema(self) -> Type[BaseModel]:
        return create_schema(self.get_name(suffix='Output'), self.OutputType)

    def as_graph(self, **kwargs) -> Graph:
        pass

class Modules:
    class Sync(Module[In, Out], ABC):
        @final
        def forward(self, data: In, **kwargs) -> Effect[Out]:
            def _invoke() -> Out:
                return self._invoke(data, **kwargs)
            return Effects.Sync(_invoke)

        @abstractmethod
        def _invoke(self, data: In, **kwargs) -> Out:
            pass

    class Async(Module[In, Out], ABC):
        @final
        def forward(self, data: In, **kwargs) -> Effect[Out]:
            async def _ainvoke() -> Out:
                return await self._ainvoke(data, **kwargs)
            return Effects.Async(_ainvoke)

        @abstractmethod
        async def _ainvoke(self, data: In, **kwargs) -> Out:
            pass

    class Stream(Module[In, Out], ABC):
        @final
        def forward(self, data: In, **kwargs) -> Effect[Out]:
            def _iter() -> Iterator[Out]:
                yield from self._iter(data, **kwargs)
            return Effects.Iterator(_iter)

        @abstractmethod
        def _iter(self, data: In, **kwargs) -> Iterator[Out]:
            pass

    class AsyncStream(Module[In, Out], ABC):
        @final
        def forward(self, data: In, **kwargs) -> Effect[Out]:
            async def _aiter() -> AsyncIterator[Out]:
                async for item in self._aiter(data, **kwargs): #type: ignore
                    yield item
            return Effects.AsyncIterator(_aiter)

        @abstractmethod
        async def _aiter(self, data: In, **kwargs) -> AsyncIterator[Out]:
            pass

ModuleFunction = Callable[[In], ReturnType[Out]] | Callable[..., ReturnType[Out]]
ModuleLike = Module[In, Out] | ModuleFunction[In, Out]

def coerce_to_module(thing: ModuleLike[In, Out]) -> Module[In, Out]:
    from modstack.modules.functional import Functional
    if isinstance(thing, Module):
        return thing
    return Functional(thing)

def module(func: ModuleFunction[In, Out]) -> Module[In, Out]:
    from modstack.modules.functional import Functional
    return Functional(func)