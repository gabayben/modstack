from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Callable, Coroutine, Generic, Iterator, Optional, TypeVar, final

from unsync import unsync

from modstack.typing.protocols import Addable
from modstack.typing.vars import Other, Out
from modstack.utils.threading import run_sync

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
            add_values: bool | None = None,
            return_last: bool | None = None
        ):
            self.func = func
            self.add_values = add_values if add_values is not None else True
            self.return_last = return_last if return_last is not None else True

        def invoke(self) -> Out:
            if self.add_values and issubclass(Out, Addable):
                current = next(self.iter())
                for value in self.iter():
                    current += value
                return current
            if not self.return_last:
                return next(self.iter())
            values = list(self.iter())
            return values[-1] if values else None

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
            add_values: bool | None = None,
            return_last: bool | None = None
        ):
            self.func = func
            self.max_workers = max_workers
            self.add_values = add_values if add_values is not None else True
            self.return_last = return_last if return_last is not None else True

        def invoke(self) -> Out:
            return run_sync(self.ainvoke(), max_workers=self.max_workers)

        async def ainvoke(self) -> Out:
            if self.add_values and issubclass(Out, Addable):
                current = await anext(self.aiter())
                async for item in self.aiter():
                    current += item
                return current
            if not self.return_last:
                return await anext(self.aiter())
            items: list[Out] = []
            async for item in self.aiter():
                items.append(item)
            return items[-1] if items else None

        def iter(self) -> Iterator[Out]:
            @unsync
            async def _aiter():
                return [item async for item in self.aiter()]
            yield from _aiter().result()

        async def aiter(self) -> AsyncIterator[Out]:
            async for item in self.func():
                yield item

    @final
    class Provide(Effect[Out]):
        def __init__(
            self,
            invoke: Optional[Callable[[], Out]] = None,
            ainvoke: Optional[Callable[[], Coroutine[Any, Any, Out]]] = None,
            iter_: Optional[Callable[[], Iterator[Out]]] = None,
            aiter_: Optional[Callable[[], AsyncIterator[Out]]] = None
        ):
            if not invoke and not ainvoke and not iter_ and not aiter_:
                raise ValueError('You must provide at least 1 function to Effects.Any.')
            self._invoke = invoke
            self._ainvoke = ainvoke
            self._iter = iter_
            self._aiter = aiter_

        def invoke(self) -> Out:
            if self._invoke:
                return self._invoke()
            elif self._ainvoke:
                return self._aforward().invoke()
            elif self._iter:
                return self._iter_forward().invoke()
            return self._aiter_forward().invoke()

        async def ainvoke(self) -> Out:
            if self._ainvoke:
                return await self._ainvoke()
            elif self._invoke:
                return self._invoke()
            elif self._aiter:
                return await self._aiter_forward().ainvoke()
            return self._iter_forward().invoke()

        def iter(self) -> Iterator[Out]:
            if self._iter:
                yield from self._iter()
            elif self._aiter:
                yield from self._aiter_forward().iter()
            elif self._invoke:
                yield self._invoke()
            yield self._aforward().invoke()

        async def aiter(self) -> AsyncIterator[Out]:
            if self._aiter:
                async for item in self._aiter():
                    yield item
            elif self._iter:
                for item in self._iter():
                    yield item
            elif self._ainvoke:
                yield await self._ainvoke()
            yield self._invoke()

        def _aforward(self) -> Effect[Out]:
            return Effects.Async(self._ainvoke)

        def _iter_forward(self) -> Effect[Out]:
            return Effects.Iterator(self._iter)

        def _aiter_forward(self) -> Effect[Out]:
            return Effects.AsyncIterator(self._aiter)

    @final
    class Map(Generic[Other, Out], Effect[Out]):
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
    class FlatMap(Generic[Other, Out], Effect[Out]):
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