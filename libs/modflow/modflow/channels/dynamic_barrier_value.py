"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/channels/dynamic_barrier_value.py
"""
from contextlib import contextmanager
from typing import Generator, NamedTuple, Optional, Self, Sequence, Type, Union

from modflow.channels import Channel, EmptyChannelError, InvalidUpdateError

type _Checkpoint[Value] = tuple[Optional[set[Value]], set[Value]]

class WaitForNames[Value](NamedTuple):
    names: set[Value]

class DynamicBarrierValue[Value](Channel[Value, Union[Value, WaitForNames[Value]], set[Value]]):
    """
    A channel that switches between two states
    - in the "priming" state it can't be read from.
        - if it receives a WaitForNames update, it switches to the "waiting" state.
    - in the "waiting" state it collects named values until all are received.
        - once all named values are received, it can be read once, and it switches
          back to the "priming" state.
    """

    names: Optional[set[Value]]
    seen: set[Value]

    @property
    def ValueType(self) -> Type[Value]:
        raise self.type_

    @property
    def UpdateType(self) -> Type[Value]:
        return self.type_

    def __init__(self, type_: Type[Value]):
        self.type_ = type_
        self.names = None
        self.seen = set()

    @contextmanager
    def new(self, checkpoint: Optional[_Checkpoint[Value]] = None) -> Generator[Self, None, None]:
        value = self.__class__(self.type_)
        if checkpoint is not None:
            names, seen = checkpoint
            value.names = names.copy() if names is not None else None
            value.seen = seen.copy()
        try:
            yield value
        finally:
            pass

    def checkpoint(self) -> _Checkpoint[Value]:
        return self.names, self.seen

    def get(self) -> Value:
        if self.names != self.seen:
            raise EmptyChannelError()
        return None

    def update(self, values: Sequence[Union[Value, WaitForNames]]) -> None:
        if self.names == self.seen:
            self.names = None
            self.seen = set()
        if wait_for_names := [v for v in values if isinstance(v, WaitForNames)]:
            if len(wait_for_names) > 1:
                raise InvalidUpdateError('Received multiple WaitForNames updates in the same step.')
            self.names = wait_for_names[0].names
        elif self.names is not None:
            for value in values:
                assert not isinstance(value, WaitForNames)
                if value in self.names:
                    self.seen.add(value)
                else:
                    raise InvalidUpdateError(f'{value} not in {self.names}')