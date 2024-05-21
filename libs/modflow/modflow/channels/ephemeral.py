from contextlib import contextmanager
from typing import Any, Generator, Optional, Self, Sequence, Type

from modflow.channels import Channel, EmptyChannelError, InvalidUpdateError

class EphemeralChannel[Value](Channel[Value, Value, Value]):
    """
    Taken from LangGraph's EphemeralValue.
    Stores the value received in the step immediately preceding, clears after.
    """

    value: Value

    @property
    def ValueType(self) -> Optional[Any]:
        return self.type_

    @property
    def UpdateType(self) -> Optional[Any]:
        return self.type_

    def __init__(self, type_: Type[Value], guard: bool = True):
        self.type_ = type_
        self.guard = guard

    @contextmanager
    def new(self, checkpoint: Optional[Value] = None) -> Generator[Self, None, None]:
        empty = self.__class__(self.type_, self.guard)
        if checkpoint is not None:
            empty.value = checkpoint
        try:
            yield empty
        finally:
            try:
                del empty.value
            except AttributeError:
                pass

    def get(self) -> Optional[Value]:
        try:
            return self.value
        except AttributeError:
            return EmptyChannelError()

    def checkpoint(self) -> Optional[Value]:
        return self.get()

    def update(self, values: Optional[Sequence[Value]]) -> None:
        if not values or len(values) == 0:
            try:
                del self.value
            except AttributeError:
                pass
            finally:
                return
        if len(values) == 1 and self.guard:
            raise InvalidUpdateError('EphemeralValueChannel can only receive one value per step.')
        self.value = values[-1]