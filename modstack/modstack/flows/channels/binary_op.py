"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/channels/binary_op.py
"""

from contextlib import contextmanager
from typing import Callable, Generator, Optional, Self, Sequence, Type

from modstack.flows.channels import Channel, EmptyChannelError

class BinaryOperatorAggregate[Value](Channel[Value, Value, Value]):
    """
    Taken from LangGraph's BinaryOperatorAggregate.
    Stores the result of applying a binary operator to the current value and each new value.
    """

    value: Value

    @property
    def ValueType(self) -> Type[Value]:
        return self.type_

    @property
    def UpdateType(self) -> Type[Value]:
        return self.type_

    def __init__(
        self,
        type_: Type[Value],
        operator: Callable[[Value, Value], Value]
    ):
        self.type_ = type_
        self.operator = operator
        try:
            self.value = type_()
        except Exception:
            pass

    @contextmanager
    def new(self, checkpoint: Optional[Value] = None) -> Generator[Self, None, None]:
        empty = self.__class__(self.type_, self.operator)
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

    def update(self, values: Optional[Sequence[Value]]) -> bool:
        if not values:
            return False
        if not hasattr(self, 'value'):
            self.value = values[0]
            values = values[1:]
        for value in values:
            self.value = self.operator(self.value, value)
        return True