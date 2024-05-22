from abc import ABC, abstractmethod
from contextlib import asynccontextmanager, contextmanager
import inspect
from typing import Any, AsyncGenerator, Generator, Generic, NamedTuple, Self, TYPE_CHECKING, Type, TypeGuard, TypeVar, Union

from modflow import PregelTaskDescription

if TYPE_CHECKING:
    from modflow.modules import Pregel

_V = TypeVar('_V')

"""
Taken from LangGraph's ManagedValue.
"""
class ManagedValue(Generic[_V], ABC):
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
    def __call__(self, step: int, task: PregelTaskDescription) -> _V:
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
) -> Generator[ManagedValue, None, None]:
    pass

@asynccontextmanager
async def AsyncManagedValuesManager(
    values: dict[str, ManagedValueSpec],
    flow: 'Pregel',
    **kwargs
) -> AsyncGenerator[ManagedValue, None]:
    pass