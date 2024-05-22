from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Callable, Coroutine, Generic, Iterator, TypeVar, final

from unsync import unsync

from modstack.typing.protocols import Addable
from modstack.typing.vars import Other, Out
from modstack.utils.coroutines import run_sync

class Effect(Generic[Out], ABC):
    def map(
        self,
        func: Callable[[Out, ...], Other],
        **kwargs
    ) -> 'Effect[Other]':
        return Effects.Map(self, func, **kwargs)

    def flat_map(
        self,
        func: Callable[[Out, ...], 'Effect[Other]'],
        **kwargs
    ) -> 'Effect[Other]':
        return Effects.FlatMap(self, func, **kwargs)

    @abstractmethod
    def invoke(self) -> Out:
        pass

    @abstractmethod
    async def ainvoke(self) -> Out:
        pass

    @abstractmethod
    def iter(self) -> Iterator[Out]:
        pass

    @abstractmethod
    async def aiter(self) -> AsyncIterator[Out]:
        pass

class Effects:
    @final
    class Value(Effect[Out]):
        def __init__(self, value: Out):
            self.value = value

        def invoke(self) -> Out:
            return self.value

        async def ainvoke(self) -> Out:
            return self.invoke()

        def iter(self) -> Iterator[Out]:
            yield self.invoke()

        async def aiter(self) -> AsyncIterator[Out]:
            yield self.invoke()

    @final
    class Sync(Effect[Out]):
        def __init__(self, func: Callable[[], Out]):
            self.func = func

        def invoke(self) -> Out:
            return self.func()

        async def ainvoke(self) -> Out:
            return self.invoke()

        def iter(self) -> Iterator[Out]:
            yield self.invoke()

        async def aiter(self) -> AsyncIterator[Out]:
            yield self.invoke()

    @final
    class Async(Effect[Out]):
        def __init__(
            self,
            func: Callable[[], Coroutine[Any, Any, Out]],
            max_workers: int | None = None
        ):
            self.func = func
            self.max_workers = max_workers

        def invoke(self) -> Out:
            return run_sync(self.ainvoke(), max_workers=self.max_workers)

        async def ainvoke(self) -> Out:
            return await self.func()

        def iter(self) -> Iterator[Out]:
            yield self.invoke()

        async def aiter(self) -> AsyncIterator[Out]:
            yield await self.ainvoke()

    @final
    class Iterator(Effect[Out]):
        def __init__(
            self,
            func: Callable[[], Iterator[Out]],
            add_values: bool = True,
            return_last: bool = True
        ):
            self.func = func
            self.add_values = add_values
            self.return_last = return_last

        def invoke(self) -> Out:
            if self.add_values and issubclass(Out, Addable):
                current: Out = next(self.iter())
                for value in self.iter():
                    current += value
                return current
            values = list(self.iter())
            if values:
                return values[-1] if self.return_last else values[0]
            return None

        async def ainvoke(self) -> Out:
            return self.invoke()

        def iter(self) -> Iterator[Out]:
            yield from self.func()

        async def aiter(self) -> AsyncIterator[Out]:
            for item in self.iter():
                yield item

    @final
    class AsyncIterator(Effect[Out]):
        def __init__(
            self,
            func: Callable[[], AsyncIterator[Out]],
            max_workers: int | None = None,
            add_values: bool = True,
            return_last: bool = True
        ):
            self.func = func
            self.max_workers = max_workers
            self.add_values = add_values
            self.return_last = return_last

        def invoke(self) -> Out:
            return run_sync(self.ainvoke(), max_workers=self.max_workers)

        async def ainvoke(self) -> Out:
            if self.add_values and issubclass(Out, Addable):
                current: Out = await anext(self.func())
                async for item in self.func():
                    current += item
                return current
            items: list[Out] = []
            async for item in self.func():
                items.append(item)
            if items:
                return items[-1] if self.return_last else items[0]
            return None

        def iter(self) -> Iterator[Out]:
            @unsync
            async def _aiter():
                return [item async for item in self.aiter()]
            yield from _aiter().result()

        async def aiter(self) -> AsyncIterator[Out]:
            async for item in self.func():
                yield item

    @final
    class Map(Generic[Out, Other], Effect[Out]):
        def __init__(
            self,
            effect: Effect[Other],
            func: Callable[[Other, ...], Out],
            **kwargs
        ):
            self.effect = effect
            self.func = func
            self.kwargs = kwargs

        def invoke(self) -> Out:
            return self.func(self.effect.invoke(), **self.kwargs)

        async def ainvoke(self) -> Out:
            return self.func(await self.effect.ainvoke(), **self.kwargs)

        def iter(self) -> Iterator[Out]:
            for item in self.effect.iter():
                yield self.func(item, **self.kwargs)

        async def aiter(self) -> AsyncIterator[Out]:
            async for item in self.effect.aiter(): #type: ignore
                yield self.func(item, **self.kwargs)

    @final
    class FlatMap(Generic[Out, Other], Effect[Out]):
        def __init__(
            self,
            effect: Effect[Other],
            func: Callable[[Other, ...], Effect[Out]],
            **kwargs
        ):
            self.effect = effect
            self.func = func
            self.kwargs = kwargs

        def invoke(self) -> Out:
            return self.func(self.effect.invoke(), **self.kwargs).invoke()

        async def ainvoke(self) -> Out:
            return await self.func(await self.effect.ainvoke(), **self.kwargs).ainvoke()

        def iter(self) -> Iterator[Out]:
            for item in self.effect.iter():
                yield self.func(item, **self.kwargs).invoke()

        async def aiter(self) -> AsyncIterator[Out]:
            async for item in self.effect.aiter(): #type: ignore
                yield await self.func(item, **self.kwargs).ainvoke()

_T = TypeVar('_T')
ReturnType = _T | Coroutine[Any, Any, _T] | Iterator[_T] | AsyncIterator[_T] | Effect[_T]