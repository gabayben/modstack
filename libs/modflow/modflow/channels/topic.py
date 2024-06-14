"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/channels/topic.py
"""

from contextlib import contextmanager
from typing import Generator, Iterator, Optional, Self, Sequence, Type, Union

from modflow.channels import Channel

class TopicValue[Value](Channel[Sequence[Value], Union[Value, list[Value]], tuple[set[Value], list[Value]]]):
    """
    A configurable PubSub Topic.

    Args:
        type_: The type of the value stored in the channel.
        unique: Whether to discard duplicate values.
        accumulate: Whether to accummulate values across steps. If False, the channel will be emptied after each step.
    """

    @property
    def ValueType(self) -> Type[Sequence[Value]]:
        return Sequence[self.type_]

    @property
    def UpdateType(self) -> Type[Union[Value, list[Value]]]:
        return Union[self.type_, list[self.type_]]

    def __init__(
        self,
        type_: Type[Value],
        unique: bool = False,
        accumulate: bool = False
    ):
        self.type_ = type_
        self.unique = unique
        self.accumulate = accumulate
        self.seen = set[Value]()
        self.values = list[Value]()

    @contextmanager
    def new(self, checkpoint: Optional[tuple[set[Value, list[Value]]]] = None) -> Generator[Self, None, None]:
        empty = self.__class__(self.type_, self.unique, self.accumulate)
        if checkpoint is not None:
            empty.seen = checkpoint[0]
            empty.values = checkpoint[1]
        try:
            yield empty
        finally:
            pass

    def checkpoint(self) -> Optional[tuple[set[Value], list[Value]]]:
        return self.seen, self.values

    def get(self) -> Optional[Sequence[Value]]:
        return list(self.values)

    def update(self, values: Optional[Sequence[Sequence[Value]]]) -> None:
        if not self.accumulate:
            self.values = list[Value]()
        if values:
            if flat_values := _flatten(values):
                if self.unique:
                    for value in flat_values:
                        if value not in self.seen:
                            self.seen.add(value)
                            self.values.append(value)
                else:
                    self.values.extend(flat_values)

def _flatten[Value](values: Sequence[Union[Value, list[Value]]]) -> Iterator[Value]:
    for value in values:
        if isinstance(value, list):
            yield from value
        else:
            yield value