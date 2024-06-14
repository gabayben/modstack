"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/pregel/__init__.py
"""

import asyncio
from collections import defaultdict, deque
from concurrent import futures
from functools import partial
import logging
from typing import Any, AsyncIterator, Iterator, Literal, Optional, Sequence, Type, Union, Unpack, final, overload, override

from pydantic import BaseModel, Field, model_validator

from modflow import All, FlowInput, FlowOutput, FlowOutputChunk, FlowRecursionError, PregelExecutableTask, PregelTaskDescription, RunFlow, StateSnapshot, StreamMode
from modflow.channels import AsyncChannelManager, Channel, ChannelManager, EmptyChannelError, InvalidUpdateError
from modflow.checkpoints import Checkpoint, CheckpointMetadata, Checkpointer
from modflow.constants import READ_KEY, INTERRUPT, HIDDEN
from modflow.managed import AsyncManagedValuesManager, ManagedValueSpec, ManagedValuesManager, is_managed_value
from modflow.modules import PregelNode
from modflow.utils.checkpoints import copy_checkpoint, create_checkpoint, empty_checkpoint
from modflow.utils.debug import map_debug_checkpoint, map_debug_task_results, map_debug_tasks, print_step_checkpoint, print_step_tasks, print_step_writes
from modflow.utils.io import map_input, map_output_updates, map_output_values, read_channel, read_channels
from modflow.utils.validation import validate_flow, validate_keys
from modstack.modules import Sequential, SerializableModule
from modstack.typing import Effect, Effects
from modstack.utils.serialization import create_model
from modstack.utils.threading import get_executor

logger = logging.getLogger(__name__)

class Pregel(SerializableModule[FlowInput, FlowOutput]):
    nodes: dict[str, PregelNode]
    channels: dict[str, Channel]
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
    def InputType(self) -> Type[Any]:
        if isinstance(self.input_channels, str):
            return self.channels[self.input_channels].UpdateType
        return super().InputType
    
    @property
    @override
    def OutputType(self) -> Type[Any]:
        if isinstance(self.output_channels, str):
            return self.channels[self.output_channels].ValueType
        return super().OutputType

    @property
    def stream_channels_asis(self) -> Union[str, Sequence[str]]:
        return self.stream_channels or [k for k in self.channels.keys()]

    @property
    def stream_channels_list(self) -> list[str]:
        return [[self.stream_channels] if isinstance(self.stream_channels, str) else self.stream_channels]

    @property
    def managed_values_dict(self) -> dict[str, ManagedValueSpec]:
        return {
            k: v
            for node in self.nodes.values()
            if isinstance(node.channels, dict)
            for k, v in node.channels.items()
            if is_managed_value(v)
        }

    @classmethod
    @model_validator(mode='before')
    def validate_on_init(cls, data: dict[str, Any]) -> dict[str, Any]:
        validate_flow(
            nodes=data['nodes'],
            channels=data['channels'],
            input_channels=data['input_channels'],
            output_channels=data['output_channels'],
            stream_channels=data['stream_channels'],
            interrupt_before=data['interrupt_before_nodes'],
            interrupt_after=data['interrupt_after_nodes']
        )
        if (data['interrupt_before_nodes'] or data['interrupt_after_nodes']) and not data['checkpointer']:
            raise ValueError('Interrupts require a checkpointer.')
        return data

    def validate_flow(self) -> None:
        validate_flow(
            nodes=self.nodes,
            channels=self.channels,
            input_channels=self.input_channels,
            output_channels=self.output_channels,
            stream_channels=self.stream_channels,
            interrupt_before=self.interrupt_before,
            interrupt_after=self.interrupt_after
        )

    def get_state(self, **kwargs) -> StateSnapshot:
        self._validate_checkpointer()
        saved = self.checkpointer.get(**kwargs)
        checkpoint = saved.checkpoint if saved else empty_checkpoint()
        kwargs = saved.config if saved else kwargs
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
        saved = await self.checkpointer.aget(**kwargs)
        checkpoint = saved.checkpoint if saved else empty_checkpoint()
        kwargs = saved.config if saved else kwargs
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
        for checkpoint, metadata, other_kwargs in self.checkpointer.get_list(**kwargs):
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
        saved = self.checkpointer.get(**kwargs)
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
                create_checkpoint(checkpoint, channels, step),
                CheckpointMetadata(
                    source='update',
                    step=step,
                    writes={as_node: values}
                ),
                **(saved.config if saved else kwargs)
            )

    async def aupdate_state(
        self,
        values: Union[dict[str, Any], Any],
        as_node: Optional[str] = None,
        **kwargs
    ) -> dict[str, Any]:
        self._validate_checkpointer()
        saved = await self.checkpointer.aget(**kwargs)
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
                create_checkpoint(checkpoint, channels, step),
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

    def _validate_checkpointer(self) -> None:
        if not self.checkpointer:
            raise ValueError('No checkpointer set.')

    @final
    def forward(self, inputs: FlowInput, **kwargs) -> Effect[FlowOutput]:
        return Effects.Provide(
            invoke=partial(self._invoke, inputs, **kwargs),
            ainvoke=partial(self._ainvoke, inputs, **kwargs),
            iter_=partial(self._iter, inputs, **kwargs),
            aiter_=partial(self._aiter, inputs, **kwargs)
        )

    def _invoke(self, inputs: FlowInput, **kwargs: Unpack[RunFlow]) -> FlowOutput:
        if kwargs['stream_mode'] == 'values':
            latest: FlowOutputChunk = None
        else:
            chunks: list[FlowOutputChunk] = []
        for chunk in self._iter(inputs, **kwargs):
            latest = chunk
            chunks.append(chunk)
        if kwargs['stream_mode'] == 'values':
            return latest
        return chunks

    async def _ainvoke(self, inputs: FlowInput, **kwargs: Unpack[RunFlow]) -> FlowOutput:
        if kwargs['stream_mode'] == 'values':
            latest: FlowOutputChunk = None
        else:
            chunks: list[FlowOutputChunk] = []
        async for chunk in self._aiter(inputs, **kwargs): #type: ignore
            latest = chunk
            chunks.append(chunk)
        if kwargs['stream_mode'] == 'values':
            return latest
        return chunks

    def _iter(self, inputs: FlowInput, **kwargs: Unpack[RunFlow]) -> Iterator[FlowOutput]:
        self._set_defaults(**kwargs)
        try:
            config = kwargs['config']
            self._validate_config(config)
            background_tasks: list[futures.Future] = []
            # copy nodes to ignore mutations during execution
            processes: dict[str, PregelNode] = {**self.nodes}
            saved = self.checkpointer.get(**config) if self.checkpointer else None
            checkpoint = saved.checkpoint if saved else empty_checkpoint()
            checkpoint_config = saved.config if saved else config
            start = saved.metadata.get('step', -2) + 1 if saved else -1
            recursion_limit = config['recursion_limit']
            # create channels from checkpoint
            with (
                ChannelManager(self.channels, checkpoint) as channels,
                ManagedValuesManager(self.managed_values_dict, self, **config) as managed_values,
                get_executor() as executor
            ):
                # map inputs to channel updates
                if input_writes := deque(map_input(kwargs['input_keys'], inputs)):
                    # discard any unfinished tasks from previous checkpoint
                    checkpoint, _ = _prepare_next_tasks(
                        checkpoint,
                        processes,
                        channels,
                        managed_values,
                        -1,
                        for_execution=True,
                        **config
                    )
                    # apply input writes
                    _apply_writes(checkpoint, channels, input_writes)
                    # save input checkpoint
                    if self.checkpointer is not None:
                        checkpoint = create_checkpoint(checkpoint, channels, start)
                        background_tasks.append(
                            executor.submit(
                                self.checkpointer.put,
                                checkpoint,
                                CheckpointMetadata(source='input', step=start, writes=inputs),
                                **config
                            )
                        )
                        checkpoint_config = {**checkpoint_config, 'thread_ts': checkpoint['id']}
                    start += 1
                else:
                    # if no input received, take that as a signal to proceed past previous interrupt, if any
                    checkpoint = copy_checkpoint(checkpoint)
                    for chan in self.stream_channels_list:
                        checkpoint['versions_seen'][INTERRUPT][chan] = checkpoint['channel_versions'][chan]

                # Similarly to Bulk Synchronous Parallel / Pregel model
                # computation proceeds in steps, while there are channel updates.
                # Channel updates from step N are only visible in step N+1.
                # Channels are guaranteed to be immutable for the duration of the step,
                # with channel updates applied only at the transition between steps.
                stop = start + recursion_limit + 1
                for step in range(start, stop):
                    next_checkpoint, next_tasks = _prepare_next_tasks(
                        checkpoint,
                        processes,
                        channels,
                        managed_values,
                        step,
                        for_execution=True,
                        **config
                    )

                    # if no more tasks, we're done
                    if not next_tasks:
                        if step == start:
                            raise ValueError('No tasks to run in flow.')
                        break

                    # before execution, check if we should interrupt
                    if _should_interrupt(
                        checkpoint,
                        kwargs.interrupt_before, # type: ignore
                        self.stream_channels_list,
                        next_tasks
                    ):
                        break
                    checkpoint = next_checkpoint

                    if kwargs['debug']:
                        print_step_tasks(step, next_tasks)
                    if kwargs['stream_mode'] == 'debug':
                        for chunk in map_debug_tasks(step, next_tasks):
                            yield chunk

                    futures_ = [
                        executor.submit(task.process.invoke, task.data, **task.kwargs)
                        for task in next_tasks
                    ]

                    # execute tasks, and wait for one to fail or all to finish.
                    # each task is independent from all other concurrent tasks.
                    done, inflight = futures.wait(
                        futures_,
                        timeout=self.step_timeout,
                        return_when=futures.FIRST_EXCEPTION
                    )

                    # panic on failure or timeout
                    _panic_or_proceed(done, inflight, step)

                    # combine pending writes from all tasks
                    pending_writes: deque[tuple[str, Any]] = deque()
                    for task in next_tasks:
                        pending_writes.extend(task.writes)

                    if kwargs['debug']:
                        print_step_writes(step, pending_writes, self.stream_channels_list)

                    _apply_writes(checkpoint, channels, pending_writes)

                    if kwargs['debug']:
                        print_step_checkpoint(step, channels, self.stream_channels_list)

                    # map and yield current value or updates
                    if kwargs['stream_mode'] == 'values':
                        mapped_values = map_output_values(kwargs['output_keys'], pending_writes, channels)
                        yield mapped_values
                    elif kwargs['stream_mode'] == 'updates':
                        mapped_updates = map_output_updates(kwargs['output_keys'], next_tasks)
                        yield from mapped_updates
                    else:
                        mapped_debug_task_results = map_debug_task_results(step, next_tasks, self.stream_channels_list)
                        yield from mapped_debug_task_results

                    # save end of step checkpoint
                    if self.checkpointer is not None:
                        checkpoint = create_checkpoint(checkpoint, channels, step)
                        background_tasks.append(
                            executor.submit(
                                self.checkpointer.put,
                                checkpoint.copy(),
                                CheckpointMetadata(
                                    source='loop',
                                    step=step,
                                    writes=_single(mapped_updates) if kwargs['stream_mode'] == 'updates' else _single(mapped_values)
                                ),
                                **config
                            )
                        )
                        checkpoint_config = {**checkpoint_config, 'thread_ts': checkpoint['id']}

                    # yield debug checkpoint
                    if kwargs['stream_mode'] == 'debug':
                        yield map_debug_checkpoint(step, channels, self.stream_channels_asis, **config)

                    # after execution, check if we should interrupt
                    if _should_interrupt(
                        checkpoint,
                        kwargs.interrupt_after, #type: ignore
                        self.stream_channels_list,
                        next_tasks
                    ):
                        raise FlowRecursionError(
                            f'Recursion limit of {recursion_limit} reached'
                            'without hitting a stop condition. You can increase the '
                            'limit by setting the `recursion_limit` config key.'
                        )
        finally:
            # cancel any pending tasks when generator is interrupted
            try:
                for task in futures_:
                    task.cancel()
            except NameError:
                pass
            # wait for all background tasks to finish
            done, _ = futures.wait(background_tasks, return_when=futures.ALL_COMPLETED)
            for task in done:
                task.result()

    async def _aiter(self, inputs: FlowInput, **kwargs: Unpack[RunFlow]) -> AsyncIterator[FlowOutput]:
        self._set_defaults(**kwargs)
        try:
            config = kwargs['config']
            self._validate_config(config)
            background_tasks: list[asyncio.Task] = []
            # copy nodes to ignore mutations during execution
            processes: dict[str, PregelNode] = {**self.nodes}
            saved = await self.checkpointer.aget(**config) if self.checkpointer else None
            checkpoint = saved.checkpoint if saved else empty_checkpoint()
            checkpoint_config = saved.config if saved else config
            start = saved.metadata.get('step', -2) + 1 if saved else -1
            recursion_limit = config['recursion_limit']
            # create channels from checkpoint
            async with (
                AsyncChannelManager(self.channels, checkpoint) as channels,
                AsyncManagedValuesManager(self.managed_values_dict, self, **config) as managed_values
            ):
                # map inputs to channel updates
                if input_writes := deque(map_input(kwargs['input_keys'], inputs)):
                    # discard any unfinished tasks from previous checkpoint
                    checkpoint, _ = _prepare_next_tasks(
                        checkpoint,
                        processes,
                        channels,
                        managed_values,
                        -1,
                        for_execution=True,
                        **config
                    )
                    # apply input writes
                    _apply_writes(checkpoint, channels, input_writes)
                    # save input checkpoint
                    if self.checkpointer is not None:
                        checkpoint = create_checkpoint(checkpoint, channels, start)
                        background_tasks.append(
                            asyncio.create_task(
                                self.checkpointer.aput(
                                    checkpoint,
                                    CheckpointMetadata(source='input', step=start, writes=inputs),
                                    **config
                                )
                            )
                        )
                        checkpoint_config = {**checkpoint_config, 'thread_ts': checkpoint['id']}
                    start += 1
                else:
                    # if no input received, take that as a signal to proceed past previous interrupt, if any
                    checkpoint = copy_checkpoint(checkpoint)
                    for chan in self.stream_channels_list:
                        checkpoint['versions_seen'][INTERRUPT][chan] = checkpoint['channel_versions'][chan]

                # Similarly to Bulk Synchronous Parallel / Pregel model
                # computation proceeds in steps, while there are channel updates.
                # Channel updates from step N are only visible in step N+1.
                # Channels are guaranteed to be immutable for the duration of the step,
                # with channel updates applied only at the transition between steps.
                stop = start + recursion_limit + 1
                for step in range(start, stop):
                    next_checkpoint, next_tasks = _prepare_next_tasks(
                        checkpoint,
                        processes,
                        channels,
                        managed_values,
                        step,
                        for_execution=True,
                        **config
                    )

                    # if no more tasks, we're done
                    if not next_tasks:
                        if step == start:
                            raise ValueError('No tasks to run in flow.')
                        break

                    # before execution, check if we should interrupt
                    if _should_interrupt(
                        checkpoint,
                        kwargs.interrupt_before,  # type: ignore
                        self.stream_channels_list,
                        next_tasks
                    ):
                        break
                    checkpoint = next_checkpoint

                    if kwargs['debug']:
                        print_step_tasks(step, next_tasks)
                    if kwargs['stream_mode'] == 'debug':
                        for chunk in map_debug_tasks(step, next_tasks):
                            yield chunk

                    futures_ = [
                        asyncio.create_task(task.process.ainvoke(task.data, **task.kwargs))
                        for task in next_tasks
                    ]

                    # execute tasks, and wait for one to fail or all to finish.
                    # each task is independent from all other concurrent tasks.
                    done, inflight = await asyncio.wait(
                        futures_,
                        timeout=self.step_timeout,
                        return_when=asyncio.FIRST_EXCEPTION
                    )

                    # panic on failure or timeout
                    _panic_or_proceed(done, inflight, step)

                    # combine pending writes from all tasks
                    pending_writes: deque[tuple[str, Any]] = deque()
                    for task in next_tasks:
                        pending_writes.extend(task.writes)

                    if kwargs['debug']:
                        print_step_writes(step, pending_writes, self.stream_channels_list)

                    _apply_writes(checkpoint, channels, pending_writes)

                    if kwargs['debug']:
                        print_step_checkpoint(step, channels, self.stream_channels_list)

                    # map and yield current value or updates
                    if kwargs['stream_mode'] == 'values':
                        mapped_values = map_output_values(kwargs['output_keys'], pending_writes, channels)
                        for value in mapped_values:
                            yield value
                    elif kwargs['stream_mode'] == 'updates':
                        mapped_updates = map_output_updates(kwargs['output_keys'], next_tasks)
                        for value in mapped_updates:
                            yield value
                    else:
                        mapped_debug_task_results = map_debug_task_results(step, next_tasks, self.stream_channels_list)
                        for value in mapped_debug_task_results:
                            yield value

                    # save end of step checkpoint
                    if self.checkpointer is not None:
                        checkpoint = create_checkpoint(checkpoint, channels, step)
                        background_tasks.append(
                            asyncio.create_task(
                                self.checkpointer.aput(
                                    checkpoint.copy(),
                                    CheckpointMetadata(
                                        source='loop',
                                        step=step,
                                        writes=_single(mapped_updates) if kwargs['stream_mode'] == 'updates' else _single(mapped_values)
                                    ),
                                    **config
                                )
                            )
                        )
                        checkpoint_config = {**checkpoint_config, 'thread_ts': checkpoint['id']}

                    # yield debug checkpoint
                    if kwargs['stream_mode'] == 'debug':
                        yield map_debug_checkpoint(step, channels, self.stream_channels_asis, **config)

                    # after execution, check if we should interrupt
                    if _should_interrupt(
                        checkpoint,
                        kwargs.interrupt_after,  # type: ignore
                        self.stream_channels_list,
                        next_tasks
                    ):
                        raise FlowRecursionError(
                            f'Recursion limit of {recursion_limit} reached'
                            'without hitting a stop condition. You can increase the '
                            'limit by setting the `recursion_limit` config key.'
                        )
        finally:
            # cancel any pending tasks when generator is interrupted
            try:
                for task in futures_:
                    task.cancel()
                    background_tasks.append(task)
            except NameError:
                pass
            # wait for all background tasks to finish
            await asyncio.gather(*background_tasks)

    def _set_defaults(self, **data: Unpack[RunFlow]) -> None:
        if data['input_keys'] is None:
            data['input_keys'] = self.input_channels
        if data['output_keys'] is None:
            data['output_keys'] = self.stream_channels_asis
        else:
            validate_keys(data['output_keys'], self.channels)
        data['interrupt_before'] = data['interrupt_before'] or self.interrupt_before
        data['interrupt_after'] = data['interrupt_after'] or self.interrupt_after
        data['config'].setdefault('recursion_limit', 3)
        if data['config'].get(READ_KEY, None):
            data['stream_mode'] = 'values' # type: ignore
        else:
            data['stream_mode'] = data['stream_mode'] if data['stream_mode'] is not None else self.stream_mode
        data['debug'] = data['debug'] if data['debug'] is not None else self.debug

    def _validate_config(self, config: dict[str, Any]) -> None:
        if 'recursion_limit' in config:
            if config.get('recursion_limit') <= 0:
                raise ValueError('recursion_limit must be at least 1.')
        if self.checkpointer and not config:
            raise ValueError(
                f'Checkpointer requires one or more of the following keys: {[k for k in self.checkpointer.config.keys()]}'
            )

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
                (not kwargs or HIDDEN not in kwargs.get('tags', []))
                if interrupt_nodes == '*'
                else node in interrupt_nodes
            )
        )
    )

def _apply_writes(
    checkpoint: Checkpoint,
    channels: dict[str, Channel],
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

def _single[T](iterator: Iterator[T]) -> Optional[T]:
    for item in iterator:
        return item

@overload
def _prepare_next_tasks(
    checkpoint: Checkpoint,
    processes: dict[str, PregelNode],
    channels: dict[str, Channel],
    managed: dict[str, ManagedValueSpec],
    step: int,
    for_execution: Literal[False],
    **kwargs
) -> tuple[Checkpoint, list[PregelTaskDescription]]:
    ...

@overload
def _prepare_next_tasks(
    checkpoint: Checkpoint,
    processes: dict[str, PregelNode],
    channels: dict[str, Channel],
    managed: dict[str, ManagedValueSpec],
    step: int,
    for_execution: Literal[True],
    **kwargs
) -> tuple[Checkpoint, list[PregelExecutableTask]]:
    ...

def _prepare_next_tasks(
    checkpoint: Checkpoint,
    processes: dict[str, PregelNode],
    channels: dict[str, Channel],
    managed: dict[str, ManagedValueSpec],
    step: int,
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