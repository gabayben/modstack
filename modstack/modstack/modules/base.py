from abc import ABC, abstractmethod
from typing import AsyncIterator, Callable, Generic, Iterator, Type, final, get_args

from pydantic import BaseModel

from modstack.typing import Effect, Effects, ReturnType
from modstack.typing.vars import In, Out
from modstack.utils.serialization import create_schema

class Module(Generic[In, Out], ABC):
    name: str | None = None

    @property
    def InputType(self) -> Type[In]:
        return type(In)

    @property
    def OutputType(self) -> Type[Out]:
        """
        The type of output this module accepts specified as a type annotation.
        """
        for cls in self.__class__.__orig_bases__: # type: ignore[attr-defined]
            type_args = get_args(cls)
            if type_args and len(type_args) == 2:
                return type_args[1]
        raise TypeError(
            f"Module {self.get_name()} doesn't have an inferrable OutputType."
            'Override the OutputType property to specify the output type.'
        )

    @abstractmethod
    def forward(self, data: In) -> Effect[Out]:
        pass

    @final
    def effect(self, *args, **kwargs) -> Effect[Out]:
        return self.forward(self.input_schema().model_construct(*args, **kwargs))

    @final
    def invoke(self, *args, **kwargs) -> Out:
        return self.effect(*args, **kwargs).invoke()

    @final
    async def ainvoke(self, *args, **kwargs) -> Out:
        return await self.effect(*args, **kwargs).ainvoke()

    @final
    def iter(self, *args, **kwargs) -> Iterator[Out]:
        yield from self.effect(*args, **kwargs).iter()

    @final
    async def aiter(self, *args, **kwargs) -> AsyncIterator[Out]:
        async for item in self.effect(*args, **kwargs).aiter(): #type: ignore
            yield item

    def get_name(
        self,
        name: str | None = None,
        suffix: str | None = None
    ) -> str:
        """
        Get the name of the module.
        """
        name = name or self.name or self.__class__.__name__
        if suffix:
            if name[0].isupper():
                return name + suffix.title()
            else:
                return name + '_' + suffix.lower()
        else:
            return name

    def input_schema(self) -> Type[BaseModel]:
        return self.InputType

    def output_schema(self) -> Type[BaseModel]:
        return create_schema(self.get_name(suffix='Output'), self.OutputType)

class Modules:
    class Sync(Module[In, Out], ABC):
        @final
        def forward(self, data: In) -> Effect[Out]:
            def _invoke() -> Out:
                return self._invoke(data)
            return Effects.Sync(_invoke)

        @abstractmethod
        def _invoke(self, data: In) -> Out:
            pass

    class Async(Module[In, Out], ABC):
        @final
        def forward(self, data: In) -> Effect[Out]:
            async def _ainvoke() -> Out:
                return await self._ainvoke(data)
            return Effects.Async(_ainvoke)

        @abstractmethod
        async def _ainvoke(self, data: In) -> Out:
            pass

    class Stream(Module[In, Out], ABC):
        @final
        def forward(self, data: In) -> Effect[Out]:
            def _iter() -> Iterator[Out]:
                yield from self._iter(data)
            return Effects.Iterator(_iter)

        @abstractmethod
        def _iter(self, data: In) -> Iterator[Out]:
            pass

    class AsyncStream(Module[In, Out], ABC):
        @final
        def forward(self, data: In) -> Effect[Out]:
            async def _aiter() -> AsyncIterator[Out]:
                async for item in self._aiter(data): #type: ignore
                    yield item
            return Effects.AsyncIterator(_aiter)

        @abstractmethod
        async def _aiter(self, data: In) -> AsyncIterator[Out]:
            pass

ModuleFunction = Callable[[In], ReturnType[Out]] | Callable[..., ReturnType[Out]]

def coerce_to_module(func: ModuleFunction[In, Out]) -> Module[In, Out]:
    pass

def module(func: ModuleFunction[In, Out]) -> Module[In, Out]:
    return coerce_to_module(func)