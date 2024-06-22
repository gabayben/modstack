"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/channels/named_barrier.py
"""

from contextlib import contextmanager
from typing import Any, Generator, Optional, Self, Sequence, Type, override

from modstack.flows.channels import Channel, EmptyChannelError, InvalidUpdateError

class NamedBarrierValue[Value](Channel[Value, Value, set[Value]]):
    """
    A channel that waits until all named values are received before making the value available.
    """

    @property
    def ValueType(self) -> Optional[Any]:
        return self.type_

    @property
    def UpdateType(self) -> Optional[Any]:
        return self.type_

    def __init__(self, type_: Type[Value], names: set[Value]):
        self.type_ = type_
        self.names = names
        self.seen: set[Value] = set()

    @contextmanager
    def new(self, checkpoint: Optional[set[Value]] = None) -> Generator[Self, None, None]:
        empty = self.__class__(self.type_, self.names)
        if checkpoint is not None:
            empty.seen = checkpoint.copy()
        try:
            yield empty
        finally:
            pass

    def checkpoint(self) -> Optional[set[Value]]:
        return self.seen

    def get(self) -> Optional[Value]:
        if self.names != self.seen:
            raise EmptyChannelError()
        return None

    def update(self, values: Optional[Sequence[Value]]) -> bool:
        updated = False
        if values:
            for value in values:
                if value in self.names:
                    self.seen.add(value)
                    updated = True
                else:
                    raise InvalidUpdateError(f'Value {value} not in {self.names}.')
        return updated

    @override
    def consume(self) -> bool:
        if self.names == self.seen:
            self.seen = set()
            return True
        return False