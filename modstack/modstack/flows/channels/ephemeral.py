"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/channels/ephemeral.py
"""

from contextlib import contextmanager
from typing import Any, Generator, Optional, Self, Sequence, Type

from modstack.flows.channels import Channel, EmptyChannelError, InvalidUpdateError

class EphemeralValue[Value](Channel[Value, Value, Value]):
    """
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
            raise EmptyChannelError()

    def checkpoint(self) -> Optional[Value]:
        try:
            return self.value
        except AttributeError:
            raise EmptyChannelError()

    def update(self, values: Optional[Sequence[Value]]) -> bool:
        if not values or len(values) == 0:
            try:
                del self.value
                return True
            except AttributeError:
                return False
        if len(values) != 1 and self.guard:
            raise InvalidUpdateError('EphemeralValue can only receive one value per step.')
        self.value = values[-1]
        return True