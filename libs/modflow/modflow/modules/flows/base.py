"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/pregel/__init__.py
"""

import asyncio
from collections import defaultdict, deque
from concurrent import futures
import logging
from typing import Any, AsyncIterator, Iterator, Literal, Mapping, Optional, Self, Sequence, Type, Union, final, overload, override

import networkx as nx
from pydantic import BaseModel, Field, model_validator

from modflow import All, FlowOutput, FlowOutputChunk, PregelExecutableTask, PregelTaskDescription, RunFlow, StateSnapshot, StreamMode
from modflow.channels import AsyncChannelManager, Channel, ChannelManager, EmptyChannelError, InvalidUpdateError
from modflow.checkpoints import Checkpoint, CheckpointMetadata, Checkpointer
from modflow.constants import CONFIG_KEY_READ, INTERRUPT, TAG_HIDDEN
from modflow.managed import AsyncManagedValuesManager, ManagedValueSpec, ManagedValuesManager, is_managed_value
from modflow.modules import PregelNode
from modflow.utils.checkpoints import copy_checkpoint, create_checkpoint, empty_checkpoint
from modflow.utils.io import read_channel, read_channels
from modflow.utils.validation import validate_flow, validate_keys
from modstack.modules import Sequential, SerializableModule
from modstack.typing import Effect, Effects
from modstack.typing.vars import In, Out
from modstack.utils.serialization import create_model

logger = logging.getLogger(__name__)

class Pregel(SerializableModule[RunFlow, FlowOutput]):
    nodes: Mapping[str, PregelNode]
    channels: Mapping[str, Channel]
    input_channels: Union[str, Sequence[str]]
    output_channels: Union[str, Sequence[str]]
    stream_channels: Optional[Union[str, Sequence[str]]] = None
    interrupt_before: Union[Sequence[str], All] = Field(default_factory=list)
    interrupt_after: Union[Sequence[str], All] = Field(default_factory=list)
    checkpointer: Checkpointer
    stream_mode: StreamMode = 'values'
    auto_validate: bool = True
    step_timeout: Optional[int] = None
    debug: bool = False
    
    @property
    @override
    def InputType(self) -> Type[In]:
        if isinstance(self.input_channels, str):
            return self.channels[self.input_channels].UpdateType
        return super().InputType()
    
    @property
    @override
    def OutputType(self) -> Type[Out]:
        if isinstance(self.output_channels, str):
            return self.channels[self.output_channels].ValueType
        return super().OutputType()

    @property
    def stream_channels_asis(self) -> Union[str, Sequence[str]]:
        return self.stream_channels or [k for k in self.channels.keys()]

    @property
    def managed_values_dict(self) -> dict[str, ManagedValueSpec]:
        return {
            k: v
            for node in self.nodes.values()
            if isinstance(node.channels, dict)
            for k, v in node.channels.items()
            if is_managed_value(v)
        }

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

    def get_state(self, **kwargs) -> StateSnapshot:
        self._validate_checkpointer()
        saved = self.checkpointer.get(**kwargs).invoke()
        checkpoint = saved.checkpoint if saved else empty_checkpoint()
        kwargs = saved.kwargs if saved else kwargs
        return self._get_state(checkpoint, saved.metadata if saved else None, **kwargs)

    def _get_state(self, checkpoint: Checkpoint, metadata: CheckpointMetadata, **kwargs) -> StateSnapshot:
        with (
            ChannelManager(self.channels, checkpoint) as channels,
            ManagedValuesManager(self.managed_values_dict, self, **kwargs) as managed_values
        ):
            _, next_tasks = _prepare_next_tasks(
                checkpoint,
                self.nodes,
                channels,
                managed_values,
                -1,
                for_execution=False,
                **kwargs
            )
            return StateSnapshot(
                read_channels(channels, self.stream_channels_asis),
                tuple(name for name, _ in next_tasks),
                checkpoint['timestamp'] if checkpoint else None,
                metadata,
                kwargs
            )

    async def aget_state(self, **kwargs) -> StateSnapshot:
        self._validate_checkpointer()
        saved = await self.checkpointer.get(**kwargs).ainvoke()
        checkpoint = saved.checkpoint if saved else empty_checkpoint()
        kwargs = saved.kwargs if saved else kwargs
        return await self._aget_state(checkpoint, saved.metadata if saved else None, **kwargs)

    async def _aget_state(self, checkpoint: Checkpoint, metadata: CheckpointMetadata, **kwargs) -> StateSnapshot:
        async with (
            AsyncChannelManager(self.channels, checkpoint) as channels,
            AsyncManagedValuesManager(self.managed_values_dict, self, **kwargs) as managed_values
        ):
            _, next_tasks = _prepare_next_tasks(
                checkpoint,
                self.nodes,
                channels,
                managed_values,
                -1,
                for_execution=False,
                **kwargs
            )
            return StateSnapshot(
                read_channels(channels, self.stream_channels_asis),
                tuple(name for name, _ in next_tasks),
                checkpoint['timestamp'] if checkpoint else None,
                metadata,
                kwargs
            )

    def get_state_history(self, limit: Optional[int] = None, **kwargs) -> Iterator[StateSnapshot]:
        self._validate_checkpointer()
        for checkpoint, metadata, other_kwargs in self.checkpointer.get(**kwargs).iter():
            yield self._get_state(checkpoint, metadata, **other_kwargs)

    async def aget_state_history(self, limit: Optional[int] = None, **kwargs) -> AsyncIterator[StateSnapshot]:
        self._validate_checkpointer()
        async for checkpoint, metadata, other_kwargs in self.checkpointer.get(**kwargs).aiter(): #type: ignore
            yield await self._aget_state(checkpoint, metadata, **other_kwargs)

    def update_state(
        self,
        values: Union[Any, dict[str, Any]],
        as_node: Optional[str] = None,
        **kwargs
    ) -> dict[str, Any]:
        self._validate_checkpointer()
        saved = self.checkpointer.get(**kwargs).invoke()
        checkpoint = saved.checkpoint if saved else empty_checkpoint()
        # find last node that updated the state, if not provided
        as_node = as_node if as_node is not None else self._get_node_to_update(checkpoint)
        # update channels
        with ChannelManager(self.channels, checkpoint) as channels:
            writers = self.nodes[as_node].writers
            if not writers:
                raise InvalidUpdateError(f'Node {as_node} has no writers.')
            task = PregelExecutableTask(
                as_node,
                values,
                Sequential(*writers) if len(writers) > 1 else writers[0],
                deque(),
                [INTERRUPT],
                kwargs
            )
            task.process.invoke(task.data, **kwargs)
            _apply_writes(checkpoint, channels, task.writes)
            step = saved.metadata.get('step', -2) + 1 if saved else -1
            return self.checkpointer.put(
                create_checkpoint(checkpoint, channels),
                CheckpointMetadata(
                    source='update',
                    step=step,
                    writes={as_node: values}
                ),
                **(saved.kwargs if saved else kwargs)
            )

    async def aupdate_state(
        self,
        values: Union[dict[str, Any], Any],
        as_node: Optional[str] = None,
        **kwargs
    ) -> dict[str, Any]:
        self._validate_checkpointer()
        saved = await self.checkpointer.get(**kwargs).ainvoke()
        checkpoint = saved.checkpoint if saved else empty_checkpoint()
        # find last node that updated the state, if not provided
        as_node = as_node if as_node is not None else self._get_node_to_update(checkpoint)
        # update channels
        async with AsyncChannelManager(self.channels, checkpoint) as channels:
            writers = self.nodes[as_node].writers
            if not writers:
                raise InvalidUpdateError(f'Node {as_node} has no writers.')
            task = PregelExecutableTask(
                as_node,
                values,
                Sequential(*writers) if len(writers) > 1 else writers[0],
                deque(),
                [INTERRUPT],
                kwargs
            )
            await task.process.ainvoke(task.data, **kwargs)
            _apply_writes(checkpoint, channels, task.writes)
            step = saved.metadata.get('step', -2) + 1 if saved else -1
            return await self.checkpointer.aput(
                create_checkpoint(checkpoint, channels),
                CheckpointMetadata(
                    source='update',
                    step=step,
                    writes={as_node: values}
                )
            )

    def _get_node_to_update(self, checkpoint: Checkpoint) -> str:
        if not any(
            v for vv in checkpoint['versions_seen'].values() for v in vv.values()
        ):
            if isinstance(self.input_channels, str) and self.input_channels in self.nodes:
                as_node = self.input_channels
        else:
            last_seen_by_node = sorted(
                (v, n)
                for n, seen in checkpoint['versions_seen'].items()
                for v in seen.values()
            )
            # if two nodes updated the state at the same time, it's ambiguous
            if last_seen_by_node:
                if len(last_seen_by_node) == 1:
                    as_node = last_seen_by_node[0][1]
                elif last_seen_by_node[-1][0] != last_seen_by_node[-2][0]:
                    as_node = last_seen_by_node[-1][1]
        if as_node is None:
            raise InvalidUpdateError('Ambiguous update, specify as_node.')
        return as_node

    @final
    def forward(self, data: RunFlow, **kwargs) -> Effect[FlowOutput]:
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

    def _invoke(self, data: RunFlow, **kwargs) -> FlowOutput:
        if data.stream_mode == 'values':
            latest: FlowOutputChunk = None
        else:
            chunks: list[FlowOutputChunk] = []
        for chunk in self._iter(data, **kwargs):
            latest = chunk
            chunks.append(chunk)
        if data.stream_mode == 'values':
            return latest
        return chunks

    async def _ainvoke(self, data: RunFlow, **kwargs) -> FlowOutput:
        if data.stream_mode == 'values':
            latest: FlowOutputChunk = None
        else:
            chunks: list[FlowOutputChunk] = []
        async for chunk in self._aiter(data, **kwargs): #type: ignore
            latest = chunk
            chunks.append(chunk)
        if data.stream_mode == 'values':
            return latest
        return chunks

    def _iter(self, data: RunFlow, **kwargs) -> Iterator[FlowOutput]:
        pass

    async def _aiter(self, data: RunFlow, **kwargs) -> AsyncIterator[FlowOutput]:
        pass

    def _set_defaults(self, data: RunFlow, **kwargs) -> None:
        if data.input_keys is None:
            data.input_keys = self.input_channels
        if data.output_keys is None:
            data.output_keys = self.stream_channels_asis
        else:
            validate_keys(data.output_keys, self.channels)
        data.interrupt_before = data.interrupt_before or self.interrupt_before
        data.interrupt_after = data.interrupt_after or self.interrupt_after
        if data.config.get(CONFIG_KEY_READ, None):
            data.stream_mode = 'values'
        else:
            data.stream_mode = data.stream_mode if data.stream_mode is not None else self.stream_mode
        data.debug = data.debug if data.debug is not None else self.debug

    def _validate_checkpointer(self) -> None:
        if not self.checkpointer:
            raise ValueError('No checkpointer set.')

    @override
    def input_schema(self) -> Type[BaseModel]:
        if isinstance(self.input_channels, str):
            return super().input_schema()
        return create_model(
            self.get_name(suffix='Input'),
            **{
                chan: (self.channels[chan].UpdateType, None)
                for chan in self.input_channels or self.channels.keys()
            }
        )
    
    @override
    def output_schema(self) -> Type[BaseModel]:
        if isinstance(self.output_channels, str):
            return super().output_schema()
        return create_model(
            self.get_name(suffix='Output'),
            **{
                chan: (self.channels[chan].ValueType, None)
                for chan in self.output_channels
            }
        )

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