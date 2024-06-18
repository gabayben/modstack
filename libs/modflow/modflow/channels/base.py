"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/channels/base.py
"""

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncGenerator, Generator, Mapping, Optional, Self, Sequence

from modflow.checkpoints import Checkpoint

class EmptyChannelError(Exception):
    pass

class InvalidUpdateError(Exception):
    pass

class Channel[Value, Update, C](ABC):
    @property
    @abstractmethod
    def ValueType(self) -> Any:
        """
        The type of the value stored in the channel.
        """

    @property
    @abstractmethod
    def UpdateType(self) -> Any:
        """
        The type of the update received by the channel.
        """

    @contextmanager
    @abstractmethod
    def new(self, checkpoint: Optional[C] = None) -> Generator[Self, None, None]:
        """
        Return a new identical channel, optionally initialized from a checkpoint.
        If the checkpoint contains complex data structures, they should be copied.
        """

    @asynccontextmanager
    async def anew(self, checkpoint: Optional[C] = None) -> AsyncGenerator[Self, None, None]:
        """
        Return a new identical channel, optionally initialized from a checkpoint.
        If the checkpoint contains complex data structures, they should be copied.
        """
        with self.new(checkpoint) as c:
            yield c

    @abstractmethod
    def checkpoint(self) -> Optional[C]:
        """
        Return a serializable representation of the channel's current state.
        Raises EmptyChannelError if the channel is empty (never updated yet),
        or doesn't support checkpoints.
        """

    @abstractmethod
    def get(self) -> Optional[Value]:
        """
        Return the current value of the channel.
        Raises EmptyChannelError if the channel is empty (never updated yet).
        """

    @abstractmethod
    def update(self, values: Optional[Sequence[Update]]) -> None:
        """
        Update the channel's value with the given sequence of updates.
        The order of the updates in the sequence is arbitrary.
        Raises InvalidUpdateError if the sequence of updates is invalid.
        """

@contextmanager
def ChannelManager(
    channels: Mapping[str, Channel],
    checkpoint: Checkpoint
) -> Generator[Mapping[str, Channel], None, None]:
    """
    Manage channels for the lifetime of a Pipeline invocation (multiple steps).
    """
    empty = {
        k: v.new(checkpoint)
        for k, v in channels.items()
    }
    try:
        yield {k: v.__enter__() for k, v in empty.items()}
    finally:
        for v in empty.values():
            v.__exit__(None, None, None)

@asynccontextmanager
async def AsyncChannelManager(
    channels: Mapping[str, Channel],
    checkpoint: Checkpoint
) -> AsyncGenerator[Mapping[str, Channel], None, None]:
    """
    Manage channels for the lifetime of a Pipeline invocation (multiple steps).
    """
    empty = {
        k: v.anew(checkpoint)
        for k, v in channels.items()
    }
    try:
        yield {k: await v.__aenter__() for k, v in empty.items()}
    finally:
        for v in empty.values():
            await v.__aexit__(None, None, None)