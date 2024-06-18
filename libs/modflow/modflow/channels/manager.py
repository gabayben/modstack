"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/channels/manager.py
"""

from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator, Mapping

from modflow.channels import Channel
from modflow.checkpoints import Checkpoint

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