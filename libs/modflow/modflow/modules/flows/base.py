"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/pregel/__init__.py
"""

import asyncio
from collections import defaultdict, deque
from concurrent import futures
import logging
from typing import Any, AsyncIterator, Iterator, Literal, Mapping, Optional, Self, Sequence, Union, final, overload

import networkx as nx
from pydantic import Field, model_validator

from modflow import All, FlowInput, FlowOutput, PregelExecutableTask, PregelTaskDescription
from modflow.channels import Channel, EmptyChannelError, InvalidUpdateError
from modflow.checkpoints import Checkpoint, Checkpointer
from modflow.constants import INTERRUPT, TAG_HIDDEN
from modflow.managed import ManagedValueSpec, is_managed_value
from modflow.modules import PregelNode
from modflow.utils.checkpoints import copy_checkpoint
from modflow.utils.io import read_channel
from modflow.utils.validation import validate_flow
from modstack.modules import SerializableModule
from modstack.typing import Effect, Effects

logger = logging.getLogger(__name__)

StreamMode = Literal['values', 'updates', 'debug']

class Pregel(SerializableModule[FlowInput, FlowOutput]):
    nodes: Mapping[str, PregelNode]
    channels: Mapping[str, Channel]
    input_channels: Union[str, Sequence[str]]
    output_channels: Union[str, Sequence[str]]
    stream_channels: Optional[Union[str, Sequence[str]]] = None
    interrupt_before_nodes: Union[Sequence[str], All] = Field(default_factory=list)
    interrupt_after_nodes: Union[Sequence[str], All] = Field(default_factory=list)
    checkpointer: Checkpointer
    stream_mode: StreamMode = 'values'
    auto_validate: bool = True
    step_timeout: Optional[int] = None

    def __init__(self):
        self.graph = nx.MultiDiGraph()

    @classmethod
    @model_validator(mode='before')
    def validate_on_init(cls, data: dict[str, Any]) -> dict[str, Any]:
        validate_flow(
            nodes=data['nodes'],
            channels=data['channels'],
            default_channel_type=data['default_channel_type'],
            input_channels=data['input_channels'],
            output_channels=data['output_channels'],
            stream_channels=data['stream_channels'],
            interrupt_before_nodes=data['interrupt_before_nodes'],
            interrupt_after_nodes=data['interrupt_after_nodes']
        )
        if (data['interrupt_before_nodes'] or data['interrupt_after_nodes']) and not data['checkpointer']:
            raise ValueError('Interrupts require a checkpointer.')
        return data

    def validate(self, data: Any) -> Self:
        validate_flow(
            nodes=data['nodes'],
            channels=data['channels'],
            default_channel_type=data['default_channel_type'],
            input_channels=data['input_channels'],
            output_channels=data['output_channels'],
            stream_channels=data['stream_channels'],
            interrupt_before_nodes=data['interrupt_before_nodes'],
            interrupt_after_nodes=data['interrupt_after_nodes']
        )
        return self

    @final
    def forward(self, data: FlowInput, **kwargs) -> Effect[FlowOutput]:
        def invoke() -> FlowOutput:
            return self._invoke(data, **kwargs)

        async def ainvoke() -> FlowOutput:
            return await self._ainvoke(data, **kwargs)

        def iter_() -> Iterator[FlowOutput]:
            yield from self._iter(data, **kwargs)

        async def aiter_() -> AsyncIterator[FlowOutput]:
            async for item in self._aiter(data, **kwargs): #type: ignore
                yield item

        return Effects.Provide(
            invoke=invoke,
            ainvoke=ainvoke,
            iter_=iter_,
            aiter_=aiter_
        )

    def _invoke(self, data: FlowInput, **kwargs) -> FlowOutput:
        pass

    async def _ainvoke(self, data: FlowInput, **kwargs) -> FlowOutput:
        pass

    def _iter(self, data: FlowInput, **kwargs) -> Iterator[FlowOutput]:
        pass

    async def _aiter(self, data: FlowInput, **kwargs) -> AsyncIterator[FlowOutput]:
        pass

def _panic_or_proceed(
    done: Union[set[futures.Future[Any]], set[asyncio.Task[Any]]],
    inflight: Union[set[futures.Future[Any]], set[asyncio.Task[Any]]],
    step: int
) -> None:
    while done:
        if e := done.pop().exception():
            while inflight:
                inflight.pop().cancel()
            raise e
    if inflight:
        while inflight:
            inflight.pop().cancel()
        raise TimeoutError(f'Timed out at step {step}.')

def _should_interrupt(
    checkpoint: Checkpoint,
    interrupt_nodes: Union[Sequence[str], All],
    snapshot_channels: Sequence[str],
    tasks: list[PregelExecutableTask]
) -> bool:
    seen = checkpoint['versions_seen'].copy()[INTERRUPT].copy()
    return (
        any(
            checkpoint['channel_versions'][chan] > seen[chan]
            for chan in snapshot_channels
        )
        and any(
            node
            for node, _, _, _, _, kwargs in tasks
            if (
                (not kwargs or TAG_HIDDEN not in kwargs.get('tags', []))
                if interrupt_nodes == '*'
                else node in interrupt_nodes
            )
        )
    )

def _apply_writes(
    checkpoint: Checkpoint,
    channels: Mapping[str, Channel],
    pending_writes: Sequence[tuple[str, Any]]
) -> None:
    pending_writes_by_channel: dict[str, list[Any]] = defaultdict(list)
    for chan, value in pending_writes:
        pending_writes_by_channel[chan].append(value)

    if checkpoint['channel_versions']:
        max_version = max(checkpoint['channel_versions'].values())
    else:
        max_version = 0

    updated_channels: set[str] = set()
    for chan, writes in pending_writes_by_channel.items():
        if chan in channels:
            try:
                channels[chan].update(writes)
            except InvalidUpdateError as e:
                raise InvalidUpdateError(
                    f'Invalid update for channel {chan}: {e}.'
                ) from e
            checkpoint['channel_versions'][chan] = max_version + 1
            updated_channels.add(chan)
        else:
            logger.warning(f'Skipping write for channel {chan} which has no readers.')

    for chan in channels:
        if chan not in updated_channels:
            channels[chan].update([])

@overload
def _prepare_next_tasks(
    checkpoint: Checkpoint,
    processes: Mapping[str, PregelNode],
    channels: Mapping[str, Channel],
    managed: dict[str, ManagedValueSpec],
    step: int,
    for_execution: Literal[False],
    **kwargs
) -> tuple[Checkpoint, list[PregelTaskDescription]]:
    ...

@overload
def _prepare_next_tasks(
    checkpoint: Checkpoint,
    processes: Mapping[str, PregelNode],
    channels: Mapping[str, Channel],
    managed: dict[str, ManagedValueSpec],
    step: int,
    for_execution: Literal[True],
    **kwargs
) -> tuple[Checkpoint, list[PregelExecutableTask]]:
    ...

def _prepare_next_tasks(
    checkpoint: Checkpoint,
    processes: Mapping[str, PregelNode],
    channels: Mapping[str, Channel],
    managed: dict[str, ManagedValueSpec],
    step: int,
    *
    for_execution: bool,
    **kwargs
) -> tuple[Checkpoint, Union[list[PregelTaskDescription], list[PregelExecutableTask]]]:
    # Check if any processes should be run in next step
    # If so, prepare the values to be passed to them
    checkpoint = copy_checkpoint(checkpoint)
    tasks: list[Union[PregelTaskDescription, PregelExecutableTask]]
    for name, process in processes.items():
        seen = checkpoint['versions_seen'][name]
        # If any of the channels read by this process were updated
        if triggers := [
            chan
            for chan in process.triggers
            if not (
                isinstance(
                    read_channel(channels, chan, return_exception=True),
                    EmptyChannelError
                )
                and checkpoint['channel_versions'][chan] > seen[chan]
            )
        ]:
            # If all trigger channels subscribed by this process are not empty
            # invoke the process with the values of all non-empty channels
            if isinstance(process.channels, dict):
                try:
                    value = {
                        k: read_channel(channels, chan, catch=chan not in process.triggers)
                        for k, chan in process.channels
                        if isinstance(chan, str)
                    }

                    managed_values = {}
                    for key, chan in process.channels.items():
                        if is_managed_value(chan):
                            managed_values[key] = managed[key](step, PregelTaskDescription(name, value))

                    value.update(managed_values)
                except EmptyChannelError:
                    continue
            elif isinstance(process.channels, list):
                for chan in process.channels:
                    try:
                        value = read_channel(channels, chan, catch=False)
                        break
                    except EmptyChannelError:
                        pass
                else:
                    continue
            else:
                raise TypeError(
                    f'Invalid channels type for process. Expected dict or list, got {process.channels}.'
                )

            # If the process has a mapper, apply it to the value
            if process.mapper:
                value = process.mapper(value)

            # update seen versions
            if for_execution:
                for chan in process.channels:
                    seen.update({
                        chan: checkpoint['channel_versions'][chan]
                        for chan in process.triggers
                    })

            if for_execution:
                if node := process.get_node():
                    writes = deque()
                    tasks.append(
                        PregelExecutableTask(
                            name=name,
                            data=value,
                            process=node,
                            writes=writes,
                            triggers=triggers,
                            kwargs=kwargs
                        )
                    )
            else:
                tasks.append(PregelTaskDescription(name, value))

    return checkpoint, tasks