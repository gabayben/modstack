from contextlib import contextmanager
from typing import Any, Generator, Optional, Self, Sequence, Type

from modflow.channels import Channel, EmptyChannelError, InvalidUpdateError

class LastValue[Value](Channel[Value, Value, Value]):
    """
    Taken from LangGraph's LastValue.
    Stores the last value received, can receive at most one value per step.
    """

    value: Value

    @property
    def ValueType(self) -> Optional[Any]:
        return self.type_

    @property
    def UpdateType(self) -> Optional[Any]:
        return self.type_

    def __init__(self, type_: Type[Value]):
        self.type_ = type_

    @contextmanager
    def new(self, checkpoint: Optional[Value] = None) -> Generator[Self, None, None]:
        empty = self.__class__(self.type_)
        if checkpoint is not None:
            empty.value = checkpoint
        try:
            yield empty
        finally:
            try:
                del empty.value
            except AttributeError:
                pass

    def checkpoint(self) -> Optional[Value]:
        return self.get()

    def get(self) -> Optional[Value]:
        try:
            return self.value
        except AttributeError:
            raise EmptyChannelError()

    def update(self, values: Optional[Sequence[Value]]) -> None:
        if not values or len(values) == 0:
            return
        if len(values) != 1:
            raise InvalidUpdateError('LastValue can only receive one value per step.')
        self.value = values[-1]