from abc import ABC, abstractmethod
from functools import partial
from typing import Any, AsyncIterator, Callable, Generic, Iterator, Mapping, Sequence, TYPE_CHECKING, Type, Union, final, get_args

from pydantic import BaseModel

from modstack.modules import ModuleLike
from modstack.typing import AfterRetryFailure, Effect, Effects, RetryStrategy, ReturnType, Serializable, StopStrategy, WaitStrategy
from modstack.typing.vars import In, Out, Other
from modstack.utils.serialization import create_schema, from_dict

if TYPE_CHECKING:
    from modstack.graphs.base import Graph, AsGraph
else:
    Graph = Any
    AsGraph = Any

class Module(Generic[In, Out], AsGraph, ABC):
    name: str | None = None
    description: str | None = None

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

    def __or__(self, other: Union['ModuleLike[Out, Other]', 'ModuleMapping[Out]']) -> 'Module[In, Other]':
        from modstack.modules.sequential import Sequential
        return Sequential(self, coerce_to_module(other))

    def __ror__(self, other: 'ModuleLike[Other, In]') -> 'Module[Other, Out]':
        from modstack.modules.sequential import Sequential
        return Sequential(coerce_to_module(other), self)

    def map(self, mapper: ModuleLike[Out, Other]) -> 'Module[In, Other]':
        return self | mapper

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
        async for item in self.forward(data, **kwargs).aiter(): #type: ignore
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

    def get_description(self, description: str | None = None) -> str:
        return description or self.description or self.__doc__ or ''

    def input_schema(self) -> Type[BaseModel]:
        return create_schema(self.get_name(suffix='Input'), self.InputType)

    def output_schema(self) -> Type[BaseModel]:
        return create_schema(self.get_name(suffix='Output'), self.OutputType)

    def as_graph(self, **kwargs) -> Graph:
        pass

    def construct_input(self, data: dict[str, Any]) -> In:
        return from_dict(data, self.input_schema())

class SerializableModule(Serializable, Module[In, Out], ABC):
    pass

class Modules:
    class Sync(SerializableModule[In, Out], ABC):
        @final
        def forward(self, data: In, **kwargs) -> Effect[Out]:
            return Effects.Sync(partial(self._invoke, data, **kwargs))

        @abstractmethod
        def _invoke(self, data: In, **kwargs) -> Out:
            pass

    class Async(SerializableModule[In, Out], ABC):
        @final
        def forward(self, data: In, **kwargs) -> Effect[Out]:
            return Effects.Async(partial(self._ainvoke, data, **kwargs))

        @abstractmethod
        async def _ainvoke(self, data: In, **kwargs) -> Out:
            pass

    class Stream(SerializableModule[In, Out], ABC):
        def __init__(
            self,
            add_values: bool | None = None,
            return_last: bool | None = None,
            **kwargs
        ):
            super().__init__(**kwargs)
            self.add_values = add_values
            self.return_last = return_last

        @final
        def forward(self, data: In, **kwargs) -> Effect[Out]:
            return Effects.Iterator(
                partial(self._iter, data, **kwargs),
                add_values=self.add_values,
                return_last=self.return_last
            )

        @abstractmethod
        def _iter(self, data: In, **kwargs) -> Iterator[Out]:
            pass

    class AsyncStream(SerializableModule[In, Out], ABC):
        def __init__(
            self,
            add_values: bool | None = None,
            return_last: bool | None = None,
            **kwargs
        ):
            super().__init__(**kwargs)
            self.add_values = add_values
            self.return_last = return_last

        @final
        def forward(self, data: In, **kwargs) -> Effect[Out]:
            return Effects.AsyncIterator(
                partial(self._aiter, data, **kwargs),
                add_values=self.add_values,
                return_last=self.return_last
            )

        @abstractmethod
        async def _aiter(self, data: In, **kwargs) -> AsyncIterator[Out]:
            pass

ModuleFunction = Union[Callable[[In], ReturnType[Out]], Callable[..., ReturnType[Out]]]
ModuleLike = Union[Module[In, Out], ModuleFunction[In, Out]]
ModuleMapping = Mapping[str, ModuleLike[In, Any]]

def coerce_to_module(thing: ModuleLike[In, Out]) -> Module[In, Out]:
    from modstack.modules.functional import Functional
    if isinstance(thing, Module):
        return thing
    return Functional(thing)

def module(
    func: ModuleFunction[In, Out] | None = None,
    name: str | None = None,
    description: str | None = None,
    input_schema: Type[BaseModel] | None = None,
    output_schema: Type[BaseModel] | None = None
) -> Module[In, Out]:
    from modstack.modules.functional import Functional
    def wrapper(fn: ModuleFunction[In, Out]) -> Module[In, Out]:
        return Functional(
            fn,
            name=name,
            description=description,
            input_schema=input_schema,
            output_schema=output_schema
        )
    return wrapper(func) if func else wrapper