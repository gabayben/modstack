import inspect
from typing import AsyncIterator, Iterator, Type, final, override

from pydantic import BaseModel

from modstack.modules import Module, ModuleFunction
from modstack.typing import Effect, Effects
from modstack.typing.vars import In, Out
from modstack.utils.reflection import get_callable_type

@final
class Functional(Module[In, Out]):
    def __init__(self, func: ModuleFunction[In, Out]):
        self.callable_type = get_callable_type(func)
        signature = inspect.signature(func)
        self.parameters = {key: value for key, value in signature.parameters.items() if value.annotation != inspect.Parameter.empty}
        self._func = func

    def forward(self, data: In, **kwargs) -> Effect[Out]:
        if self.callable_type == 'effect':
            return self._func(data, **kwargs)
        elif self.callable_type == 'aiter':
            async def _aiter() -> AsyncIterator[Out]:
                async for item in self._func(data, **kwargs):
                    yield item

            return Effects.AsyncIterator(_aiter)
        elif self.callable_type == 'iter':
            def _iter() -> Iterator[Out]:
                yield from self._func(data, **kwargs)

            return Effects.Iterator(_iter)
        elif self.callable_type == 'ainvoke':
            async def _ainvoke() -> Out:
                return await self._func(data, **kwargs)

            return Effects.Async(_ainvoke)

        def _invoke() -> Out:
            return self._func(data, **kwargs)

        return Effects.Sync(_invoke)

    @override
    def get_name(
        self,
        name: str | None = None,
        suffix: str | None = None
    ) -> str:
        return super().get_name(name=self._func.__name__, suffix=suffix)

    @override
    def input_schema(self) -> Type[BaseModel]:
        return list(self.parameters.values())[0].annotation