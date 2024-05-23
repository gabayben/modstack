"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/pregel/io.py
"""

from collections import deque
from typing import Any, Iterator, Mapping, Optional, Sequence, Union

from modflow import FlowOutputChunk, PregelExecutableTask
from modflow.channels import Channel, EmptyChannelError
from modflow.constants import TAG_HIDDEN
from modstack.typing import AddableDict

def read_channel(
    channels: Mapping[str, Channel],
    channel: str,
    catch: bool = True,
    return_exception: bool = False
) -> Any | BaseException:
    try:
        return channels[channel].get()
    except EmptyChannelError as e:
        if return_exception:
            return e
        elif catch:
            return None
        raise

def read_channels(
    channels: Mapping[str, Channel],
    select: Union[str, list[str]],
    skip_empty: bool = True
) -> Union[Any, dict[str, Any]]:
    if isinstance(select, str):
        return read_channel(channels, select)
    values: dict[str, Any] = {}
    for channel in select:
        try:
            values[channel] = read_channel(channels, channel, catch = not skip_empty)
        except EmptyChannelError:
            pass
    return values

def map_input(
    input_channels: Union[str, Sequence[str]],
    chunk: Optional[Union[Any, dict[str, Any]]]
) -> Iterator[tuple[str, Any]]:
    pass

class AddableValuesDict(AddableDict):
    def __or__(self, other: dict[str, Any]) -> 'AddableValuesDict':
        return self | other

    def __ror__(self, other: dict[str, Any]) -> 'AddableValuesDict':
        return other | self

def map_output_values(
    output_channels: Union[str, Sequence[str]],
    pending_writes: deque[tuple[str, Any]],
    channels: Mapping[str, Channel]
) -> Iterator[FlowOutputChunk]:
    if isinstance(output_channels, str):
        if any(chan == output_channels for chan, _ in pending_writes):
            yield read_channel(channels, output_channels)
    else:
        if {c for c, _ in pending_writes if c in output_channels}:
            yield AddableValuesDict(read_channels(channels, output_channels)) #type: ignore[call-args]

class AddableUpdatesDict(AddableDict):
    def __add__(self, other: dict[str, Any]) -> 'AddableUpdatesDict':
        return [self, other] # type: ignore

    def __radd__(self, other: 'AddableUpdatesDict') -> 'AddableUpdatesDict':
        raise TypeError('AddableUpdatesDict does not support right-side addition.')

def map_output_updates(
    output_channels: Union[str, Sequence[str]],
    tasks: list[PregelExecutableTask]
) -> Iterator[dict[str, FlowOutputChunk]]:
    output_tasks = [t for t in tasks if not t.kwargs or TAG_HIDDEN not in t.kwargs.get('tags', [])]
    if isinstance(output_channels, str):
        if updated := AddableUpdatesDict({
            task.name: value
            for task in output_tasks
            for chan, value in task.writes
            if chan == output_channels
        }):
            yield updated
    else:
        if updated := AddableUpdatesDict({
            task.name: {chan: value for chan, value in task.writes if chan in output_channels}
            for task in output_tasks
            if any(chan in output_channels for chan, _ in task.writes)
        }):
            yield updated