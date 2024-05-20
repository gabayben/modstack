from abc import ABC, abstractmethod
from typing import AsyncIterator, Callable, Generic, Iterator, Type, final, get_args

from pydantic import BaseModel

from modstack.typing import Effect, Effects
from modstack.typing.vars import Out
from modstack.utils.serialization import create_schema, model_from_callable

class Module(Generic[Out], ABC):
    name: str | None = None

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
    def forward(self, *args, **kwargs) -> Effect[Out]:
        pass

    @final
    def invoke(self, *args, **kwargs) -> Out:
        return self.forward(*args, **kwargs).invoke()

    @final
    async def ainvoke(self, *args, **kwargs) -> Out:
        return await self.forward(*args, **kwargs).ainvoke()

    @final
    def iter(self, *args, **kwargs) -> Iterator[Out]:
        yield from self.forward(*args, **kwargs).iter()

    @final
    async def aiter(self, *args, **kwargs) -> AsyncIterator[Out]:
        async for item in self.forward(*args, **kwargs).aiter(): #type: ignore
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
        return model_from_callable(self.get_name(suffix='Input'), self.forward)

    def output_schema(self) -> Type[BaseModel]:
        return create_schema(self.get_name(suffix='Output'), self.OutputType)

class Modules:
    class Sync(Module[Out], ABC):
        @final
        def forward(self, *args, **kwargs) -> Effect[Out]:
            def _invoke() -> Out:
                return self._invoke(*args, **kwargs)
            return Effects.Sync(_invoke)

        @abstractmethod
        def _invoke(self, *args, **kwargs) -> Out:
            pass

        def input_schema(self) -> Type[BaseModel]:
            return model_from_callable(self.get_name(suffix='Input'), self._invoke)

    class Async(Module[Out], ABC):
        @final
        def forward(self, *args, **kwargs) -> Effect[Out]:
            async def _ainvoke() -> Out:
                return await self._ainvoke(*args, **kwargs)
            return Effects.Async(_ainvoke)

        @abstractmethod
        async def _ainvoke(self, *args, **kwargs) -> Out:
            pass

        def input_schema(self) -> Type[BaseModel]:
            return model_from_callable(self.get_name(suffix='Input'), self._ainvoke)

    class Stream(Module[Out], ABC):
        @final
        def forward(self, *args, **kwargs) -> Effect[Out]:
            def _iter() -> Iterator[Out]:
                yield from self._iter(*args, **kwargs)
            return Effects.Iterator(_iter)

        @abstractmethod
        def _iter(self, *args, **kwargs) -> Iterator[Out]:
            pass

        def input_schema(self) -> Type[BaseModel]:
            return model_from_callable(self.get_name(suffix='Input'), self._iter)

    class AsyncStream(Module[Out], ABC):
        @final
        def forward(self, *args, **kwargs) -> Effect[Out]:
            async def _aiter() -> AsyncIterator[Out]:
                async for item in self._aiter(*args, **kwargs): #type: ignore
                    yield item
            return Effects.AsyncIterator(_aiter)

        @abstractmethod
        async def _aiter(self, *args, **kwargs) -> AsyncIterator[Out]:
            pass

        def input_schema(self) -> Type[BaseModel]:
            return model_from_callable(self.get_name(suffix='Input'), self._aiter)

def coerce_to_module(func: Callable[[...], Out]) -> Module[Out]:
    pass

def module(func: Callable[[...], Out]) -> Module[Out]:
    pass