from abc import ABC, abstractmethod
import asyncio
from typing import Any, AsyncIterator, Callable, Coroutine, Generic, Iterator, Optional, TypeVar, final

from modstack.typing.protocols import Addable
from modstack.typing.vars import Other, Out
from modstack.utils.func import tpartial, tzip
from modstack.utils.threading import get_executor, run_async, run_async_iter, run_sync, run_sync_iter

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
            return await run_async(self.invoke)

        def iter(self) -> Iterator[Out]:
            yield self.invoke()

        async def aiter(self) -> AsyncIterator[Out]:
            yield await self.ainvoke()

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
            self.add_values = add_values if add_values is not None else False
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
            return await run_async(self.invoke)

        def iter(self) -> Iterator[Out]:
            yield from self.func()

        async def aiter(self) -> AsyncIterator[Out]:
            async for item in run_async_iter(self.iter):
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
            self.add_values = add_values if add_values is not None else False
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
            last_value: Out = None
            async for item in self.aiter():
                last_value = item
            return last_value

        def iter(self) -> Iterator[Out]:
            yield from run_sync_iter(self.aiter)

        async def aiter(self) -> AsyncIterator[Out]:
            async for item in self.func():
                yield item

    @final
    class From(Effect[Out]):
        def __init__(
            self,
            invoke: Optional[Callable[[], Out]] = None,
            ainvoke: Optional[Callable[[], Coroutine[Any, Any, Out]]] = None,
            iter_: Optional[Callable[[], Iterator[Out]]] = None,
            aiter_: Optional[Callable[[], AsyncIterator[Out]]] = None
        ):
            if not invoke and not ainvoke and not iter_ and not aiter_:
                raise ValueError('You must provide at least 1 function to Effects.From.')
            self._invoke = invoke
            self._ainvoke = ainvoke
            self._iter = iter_
            self._aiter = aiter_

        def invoke(self) -> Out:
            if self._invoke:
                return self._invoke()
            elif self._ainvoke:
                return self._async_effect().invoke()
            elif self._iter:
                return self._iter_effect().invoke()
            return self._async_iter_effect().invoke()

        async def ainvoke(self) -> Out:
            if self._ainvoke:
                return await self._ainvoke()
            elif self._invoke:
                return await run_async(self._invoke)
            elif self._aiter:
                return await self._async_iter_effect().ainvoke()
            return await self._iter_effect().ainvoke()

        def iter(self) -> Iterator[Out]:
            if self._iter:
                yield from self._iter()
            elif self._aiter:
                yield from run_sync_iter(self._aiter)
            elif self._invoke:
                yield self._invoke()
            yield self._async_effect().invoke()

        async def aiter(self) -> AsyncIterator[Out]:
            if self._aiter:
                async for item in self._aiter():
                    yield item
            elif self._iter:
                async for item in run_async_iter(self._iter):
                    yield item
            elif self._ainvoke:
                yield await self._ainvoke()
            yield await run_async(self._invoke)

        def _async_effect(self) -> Effect[Out]:
            return Effects.Async(self._ainvoke)

        def _iter_effect(self) -> Effect[Out]:
            return Effects.Iterator(self._iter)

        def _async_iter_effect(self) -> Effect[Out]:
            return Effects.AsyncIterator(self._aiter)

    @final
    class Parallel(Effect[dict[str, Any]]):
        def __init__(
            self,
            effects: dict[str, Effect[Any]],
            max_workers: Optional[int] = None
        ):
            self._effects = effects
            self._max_workers = max_workers

        def invoke(self) -> dict[str, Any]:
            with get_executor(max_workers=self._max_workers) as executor:
                futures = [
                    executor.submit(effect.invoke)
                    for effect in self._effects.values()
                ]
                return {
                    k: future.result()
                    for k, future in tzip(self._effects, futures)
                }

        async def ainvoke(self) -> dict[str, Any]:
            generators = await asyncio.gather(*(
                effect.ainvoke
                for effect in self._effects.values()
            ))
            return {
                k: v
                for k, v in zip(self._effects, generators)
            }

        def iter(self) -> Iterator[dict[str, Any]]:
            current = {}

            def iterate_effect(name: str, effect: Effect[Any]) -> Iterator[dict[str, Any]]:
                for chunk in effect.iter():
                    current[name] = chunk
                    yield current

            with get_executor(max_workers=self._max_workers) as executor:
                futures = [
                    executor.submit(
                        tpartial(iterate_effect, name, effect)
                    )
                    for name, effect in self._effects.items()
                ]
                for future in futures:
                    yield from future.result()

        async def aiter(self) -> AsyncIterator[dict[str, Any]]:
            current = {}

            async def aiterate_effect(name: str, effect: Effect[Any]) -> AsyncIterator[dict[str, Any]]:
                async for chunk in effect.aiter(): # type: ignore
                    current[name] = chunk
                    yield current

            generators = await asyncio.gather(*(
                aiterate_effect(name, effect)
                for name, effect in self._effects.items()
            ))

            for generator in generators:
                async for output in generator:
                    yield output

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