"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/managed/base.py
"""

from abc import ABC, abstractmethod
import asyncio
from contextlib import AsyncExitStack, ExitStack, asynccontextmanager, contextmanager
import inspect
from typing import Any, AsyncGenerator, Generator, Generic, NamedTuple, Self, TYPE_CHECKING, Type, TypeGuard, TypeVar, Union

from modstack.flows import PregelTaskDescription

if TYPE_CHECKING:
    pass

V = TypeVar('V')

class ManagedValue(Generic[V], ABC):
    def __init__(self, flow: 'Pregel', **kwargs):
        self.flow = flow
        self.kwargs = kwargs

    @classmethod
    @contextmanager
    def enter(cls, flow: 'Pregel', **kwargs) -> Generator[Self, None, None]:
        try:
            value = cls(flow, **kwargs)
            yield value
        finally:
            try:
                del value
            except UnboundLocalError:
                pass

    @classmethod
    @asynccontextmanager
    async def aenter(cls, flow: 'Pregel', **kwargs) -> AsyncGenerator[Self, None]:
        try:
            value = cls(flow, **kwargs)
            yield value
        finally:
            try:
                del value
            except UnboundLocalError:
                pass

    @abstractmethod
    def __call__(self, step: int, task: PregelTaskDescription) -> V:
        pass

class ConfiguredManagedValue(NamedTuple):
    cls: Type[ManagedValue]
    kwargs: dict[str, Any]

ManagedValueSpec = Union[Type[ManagedValue], ConfiguredManagedValue]

def is_managed_value(value: Any) -> TypeGuard[ManagedValueSpec]:
    return (
        (inspect.isclass(value) and issubclass(value, ManagedValue))
        or isinstance(value, ConfiguredManagedValue)
    )

@contextmanager
def ManagedValuesManager(
    values: dict[str, ManagedValueSpec],
    flow: 'Pregel',
    **kwargs
) -> Generator[dict[str, ManagedValue], None, None]:
    if values:
        with ExitStack() as stack:
            yield {
                key: stack.enter_context(
                    value.cls.enter(flow, **{**kwargs, **value.kwargs})
                    if isinstance(value, ConfiguredManagedValue)
                    else value.enter(flow, **kwargs)
                )
                for key, value in values.items()
            }
    else:
        yield {}

@asynccontextmanager
async def AsyncManagedValuesManager(
    values: dict[str, ManagedValueSpec],
    flow: 'Pregel',
    **kwargs
) -> AsyncGenerator[dict[str, ManagedValue], None]:
    if values:
        with AsyncExitStack as stack:
            tasks = {
                asyncio.create_task(
                    stack.enter_async_context(
                        value.cls.aenter(flow, **{**kwargs, **value.kwargs})
                        if isinstance(value, ConfiguredManagedValue)
                        else value.aenter(flow, **kwargs)
                    )
                ): key
                for key, value in values.items()
            }
            done, _ = await asyncio.wait(tasks)
            yield {tasks[task]: task.result() for task in done}
    else:
        yield {}