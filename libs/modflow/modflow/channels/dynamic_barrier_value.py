"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/channels/dynamic_barrier_value.py
"""

from typing import Generator, NamedTuple, Optional, Self, Sequence, Type, Union

from modflow.channels import Channel

type _Checkpoint[Value] = tuple[Optional[set[Value]], set[Value]]

class WaitForNames[Value](NamedTuple):
    names: set[Value]

class DynamicBarrierValue[Value](Channel[Value, Union[Value, WaitForNames[Value]], set[Value]]):
    @property
    def ValueType(self) -> Type[Value]:
        raise NotImplementedError()

    @property
    def UpdateType(self) -> Type[Value]:
        raise NotImplementedError()

    def new(self, checkpoint: Optional[_Checkpoint[Value]] = None) -> Generator[Self, None, None]:
        pass

    def checkpoint(self) -> _Checkpoint[Value]:
        pass

    def get(self) -> Value:
        pass

    def update(self, values: Sequence[Union[Value, WaitForNames]]) -> None:
        pass