"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/pregel/__init__.py
"""

import asyncio
from collections import defaultdict, deque
from concurrent import futures
from functools import partial
import logging
from typing import Any, AsyncIterator, Callable, Iterator, Literal, Optional, Sequence, Type, Union, Unpack, final, overload, override

from pydantic import BaseModel, Field, model_validator

from modstack.flows import All, FlowInput, FlowOutput, FlowOutputChunk, FlowRecursionError, PregelExecutableTask, PregelTaskDescription, FlowOptions, Send, StateSnapshot, StreamMode
from modstack.flows.channels import AsyncChannelManager, Channel, ChannelManager, EmptyChannelError, InvalidUpdateError
from modstack.flows.checkpoints import Checkpoint, CheckpointMetadata, Checkpointer
from modstack.flows.constants import PENDING_WRITES_CHANNEL, READ_KEY, INTERRUPT, HIDDEN, TASKS, WRITE_KEY
from modstack.flows.managed import AsyncManagedValuesManager, ManagedValueSpec, ManagedValuesManager, is_managed_value
from modstack.flows.modules import PregelNode
from modstack.flows.utils.checkpoints import copy_checkpoint, create_checkpoint, empty_checkpoint
from modstack.flows.utils.debug import map_debug_checkpoint, map_debug_task_results, map_debug_tasks, print_step_checkpoint, print_step_tasks, print_step_writes
from modstack.flows.utils.io import map_input, map_output_updates, map_output_values, read_channel, read_channels
from modstack.flows.utils.validation import validate_flow, validate_keys
from modstack.core import Sequential, SerializableModule
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

    @property
    def _get_next_version(self) -> Callable[[int, Channel], int]:
        return (
            self.checkpointer.get_next_version
            if self.checkpointer is not None
            else _increment
        )

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
        for checkpoint, metadata, other_kwargs in self.checkpointer.get_many(**kwargs):
            yield self._get_state(checkpoint, metadata, **other_kwargs)

    async def aget_state_history(self, limit: Optional[int] = None, **kwargs) -> AsyncIterator[StateSnapshot]:
        self._validate_checkpointer()
        async for checkpoint, metadata, other_kwargs in self.checkpointer.aget_many(**kwargs): #type: ignore
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
            task.process.invoke(
                task.data,
                **{
                    **kwargs,
                    WRITE_KEY: task.writes.extend,
                    READ_KEY: partial(
                        _local_read,
                        checkpoint,
                        channels,
                        task.writes
                    )
                }
            )
            # apply to checkpoint and save
            _apply_writes(checkpoint, channels, task.writes, self.checkpointer.get_next_version)
            step = saved.metadata.get('step', -2) + 1 if saved else -1

            # merge config fields with previous checkpoint config
            checkpoint_config = kwargs
            if saved:
                checkpoint_config = {**kwargs, **saved.config}

            return self.checkpointer.put(
                create_checkpoint(checkpoint, channels, step),
                CheckpointMetadata(
                    source='update',
                    step=step,
                    writes={as_node: values}
                ),
                **checkpoint_config
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
            await task.process.ainvoke(
                task.data,
                **{
                    **kwargs,
                    WRITE_KEY: task.writes.extend,
                    READ_KEY: partial(
                        _local_read,
                        checkpoint,
                        channels,
                        task.writes
                    )
                }
            )
            # apply to checkpoint and save
            _apply_writes(checkpoint, channels, task.writes, self.checkpointer.get_next_version)
            step = saved.metadata.get('step', -2) + 1 if saved else -1

            # merge config fields with previous checkpoint config
            checkpoint_config = kwargs
            if saved:
                checkpoint_config = {**kwargs, **saved.config}

            return await self.checkpointer.aput(
                create_checkpoint(checkpoint, channels, step),
                CheckpointMetadata(
                    source='update',
                    step=step,
                    writes={as_node: values}
                ),
                **checkpoint_config
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
        return Effects.From(
            invoke=partial(self._invoke, inputs, **kwargs),
            ainvoke=partial(self._ainvoke, inputs, **kwargs),
            iter_=partial(self._stream, inputs, **kwargs),
            aiter_=partial(self._astream, inputs, **kwargs)
        )

    def _invoke(self, inputs: FlowInput, **kwargs: Unpack[FlowOptions]) -> FlowOutput:
        if kwargs['stream_mode'] == 'values':
            latest: FlowOutputChunk = None
        else:
            chunks: list[FlowOutputChunk] = []
        for chunk in self._stream(inputs, **kwargs):
            latest = chunk
            chunks.append(chunk)
        if kwargs['stream_mode'] == 'values':
            return latest
        return chunks

    async def _ainvoke(self, inputs: FlowInput, **kwargs: Unpack[FlowOptions]) -> FlowOutput:
        if kwargs['stream_mode'] == 'values':
            latest: FlowOutputChunk = None
        else:
            chunks: list[FlowOutputChunk] = []
        async for chunk in self._astream(inputs, **kwargs): #type: ignore
            latest = chunk
            chunks.append(chunk)
        if kwargs['stream_mode'] == 'values':
            return latest
        return chunks

    def _stream(self, inputs: FlowInput, **kwargs: Unpack[FlowOptions]) -> Iterator[FlowOutput]:
        self._set_defaults(**kwargs)
        try:
            config = kwargs['config']
            self._validate_config(config)
            background_tasks: list[futures.Future] = []
            # copy nodes to ignore mutations during execution
            processes: dict[str, PregelNode] = {**self.nodes}
            saved = self.checkpointer.get(**config) if self.checkpointer else None
            checkpoint = saved.checkpoint if saved else empty_checkpoint()
            start = saved.metadata.get('step', -2) + 1 if saved else -1
            stream_modes = [kwargs['stream_mode']] if isinstance(kwargs['stream_mode'], str) else kwargs['stream_mode']
            recursion_limit = config['recursion_limit']

            # merge config fields with previous checkpoint config
            checkpoint_config = config
            if saved:
                checkpoint_config = {
                    **config,
                    **saved.config
                }

            # create channels from checkpoint
            with (
                ChannelManager(self.channels, checkpoint) as channels,
                ManagedValuesManager(self.managed_values_dict, self, **config) as managed_values,
                get_executor() as executor
            ):
                def put_checkpoint(metadata: CheckpointMetadata) -> Iterator[Any]:
                    nonlocal checkpoint, checkpoint_config, channels

                    if self.checkpointer is None:
                        return
                    if kwargs['debug']:
                        print_step_checkpoint(metadata['step'], channels, self.stream_channels_list)

                    # create new checkpoint
                    checkpoint = create_checkpoint(checkpoint, channels, metadata['step'])
                    # save it, without blocking
                    background_tasks.append(
                        executor.submit(
                            self.checkpointer.put,
                            copy_checkpoint(checkpoint),
                            metadata,
                            **checkpoint_config
                        )
                    )
                    # update checkpoint config
                    checkpoint_config = {**checkpoint_config, 'thread_ts': checkpoint['id']}
                    # yield debug checkpoint event
                    if 'debug' in stream_modes:
                        yield from _with_mode(
                            'debug',
                            isinstance(kwargs['stream_mode'], list),
                            map_debug_checkpoint(
                                metadata['step'],
                                channels,
                                self.stream_channels_asis,
                                **config
                            )
                        )

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
                        get_next_version=self._get_next_version,
                        **config
                    )
                    # apply input writes
                    _apply_writes(
                        checkpoint,
                        channels,
                        input_writes,
                        self._get_next_version
                    )
                    # save input checkpoint
                    yield from put_checkpoint({
                        'source': 'input',
                        'step': start,
                        'writes': inputs
                    })
                    # increment start to 0
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
                        get_next_version=self._get_next_version,
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

                    futures_ = {
                        executor.submit(task.process.invoke, task.data, **task.kwargs): task
                        for task in next_tasks
                    }

                    while futures_:
                        # execute tasks, and wait for one to fail or all to finish
                        # each task is independent from all other concurrent tasks
                        done, inflight = futures.wait(
                            futures_,
                            timeout=self.step_timeout,
                            return_when=futures.FIRST_COMPLETED
                        )
                        for future in done:
                            task = futures_.pop(future)
                            if not future.exception:
                                # we got an exception, break out of while loop
                                # exception will be handled in panic_or_proceed
                                futures_.clear()
                            else:
                                # yield updates output for the finished task
                                if 'updates' in stream_modes:
                                    yield from _with_mode(
                                        'updates',
                                        isinstance(kwargs['stream_mode'], list),
                                        map_output_updates(kwargs['output_keys'], [task])
                                    )
                                if 'debug' in stream_modes:
                                    yield from _with_mode(
                                        'debug',
                                        isinstance(kwargs['stream_mode'], list),
                                        map_debug_task_results(step, [task], self.stream_channels_list)
                                    )
                        else:
                            # remove references to loop vars
                            del future, task

                    # panic on failure or timeout
                    _panic_or_proceed(done, inflight, step)
                    # don't keep futures around in memory longer than needed
                    del futures_, done, inflight

                    # combine pending writes from all tasks
                    pending_writes: deque[tuple[str, Any]] = deque()
                    for task in next_tasks:
                        pending_writes.extend(task.writes)

                    if kwargs['debug']:
                        print_step_writes(step, pending_writes, self.stream_channels_list)

                    # apply writes to channels
                    _apply_writes(
                        checkpoint,
                        channels,
                        pending_writes,
                        self._get_next_version
                    )

                    if 'values' in stream_modes:
                        yield from _with_mode(
                            'values',
                            isinstance(kwargs['stream_mode'], list),
                            map_output_values(kwargs['output_keys'], pending_writes, channels)
                        )

                    yield from put_checkpoint({
                        'source': 'loop',
                        'step': step,
                        'writes': ( # type: ignore
                            _single(map_output_updates(kwargs['output_keys'], next_tasks))
                            if self.stream_mode == 'updates'
                            else _single(map_output_values(kwargs['output_keys'], pending_writes, channels))
                        )
                    })

                    # after execution, check if we should interrupt
                    if _should_interrupt(
                        checkpoint,
                        kwargs.interrupt_after, #type: ignore
                        self.stream_channels_list,
                        next_tasks
                    ):
                        break
                else:
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

    async def _astream(self, inputs: FlowInput, **kwargs: Unpack[FlowOptions]) -> AsyncIterator[FlowOutput]:
        self._set_defaults(**kwargs)
        try:
            config = kwargs['config']
            self._validate_config(config)
            loop = asyncio.get_event_loop()
            background_tasks: list[asyncio.Task] = []
            # copy nodes to ignore mutations during execution
            processes: dict[str, PregelNode] = {**self.nodes}
            saved = await self.checkpointer.aget(**config) if self.checkpointer else None
            checkpoint = saved.checkpoint if saved else empty_checkpoint()
            start = saved.metadata.get('step', -2) + 1 if saved else -1
            stream_modes = [kwargs['stream_mode']] if isinstance(kwargs['stream_mode'], str) else kwargs['stream_mode']
            recursion_limit = config['recursion_limit']

            # merge config fields with previous checkpoint config
            checkpoint_config = config
            if saved:
                checkpoint_config = {
                    **config,
                    **saved.config
                }

            # create channels from checkpoint
            async with (
                AsyncChannelManager(self.channels, checkpoint) as channels,
                AsyncManagedValuesManager(self.managed_values_dict, self, **config) as managed_values
            ):
                async def aput_checkpoint(metadata: CheckpointMetadata) -> AsyncIterator[Any]:
                    nonlocal checkpoint, checkpoint_config, channels

                    if self.checkpointer is None:
                        return
                    if kwargs['debug']:
                        print_step_checkpoint(metadata['step'], channels, self.stream_channels_list)

                    # create new checkpoint
                    checkpoint = create_checkpoint(checkpoint, channels, metadata['step'])
                    # save it, without blocking
                    background_tasks.append(
                        asyncio.create_task(
                            self.checkpointer.aput(
                                copy_checkpoint(checkpoint),
                                metadata,
                                **checkpoint_config
                            )
                        )
                    )
                    # update checkpoint config
                    checkpoint_config = {**checkpoint_config, 'thread_ts': checkpoint['id']}
                    # yield debug checkpoint event
                    if 'debug' in stream_modes:
                        for chunk in _with_mode(
                            'debug',
                            isinstance(kwargs['stream_mode'], list),
                            map_debug_checkpoint(
                                metadata['step'],
                                channels,
                                self.stream_channels_asis,
                                **config
                            )
                        ):
                            yield chunk

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
                        get_next_version=self._get_next_version,
                        **config
                    )
                    # apply input writes
                    _apply_writes(
                        checkpoint,
                        channels,
                        input_writes,
                        self._get_next_version
                    )
                    # save input checkpoint
                    async for chunk in aput_checkpoint({
                        'source': 'input',
                        'step': start,
                        'writes': inputs
                    }):
                        yield chunk
                    # increment start to 0
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
                        get_next_version=self._get_next_version,
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

                    futures_ = {
                        asyncio.create_task(
                            task.process.ainvoke(task.data, **task.kwargs)
                        ): task
                        for task in next_tasks
                    }

                    while futures_:
                        # execute tasks, and wait for one to fail or all to finish
                        # each task is independent from all other concurrent tasks
                        done, inflight = await asyncio.wait(
                            futures_,
                            timeout=self.step_timeout,
                            return_when=futures.FIRST_COMPLETED
                        )
                        for future in done:
                            task = futures_.pop(future)
                            if not future.exception:
                                # we got an exception, break out of while loop
                                # exception will be handled in panic_or_proceed
                                futures_.clear()
                            else:
                                # yield updates output for the finished task
                                if 'updates' in stream_modes:
                                    for chunk in _with_mode(
                                        'updates',
                                        isinstance(kwargs['stream_mode'], list),
                                        map_output_updates(kwargs['output_keys'], [task])
                                    ):
                                        yield chunk
                                if 'debug' in stream_modes:
                                    for chunk in _with_mode(
                                        'debug',
                                        isinstance(kwargs['stream_mode'], list),
                                        map_debug_task_results(step, [task], self.stream_channels_list)
                                    ):
                                        yield chunk
                        else:
                            # remove references to loop vars
                            del future, task

                    # panic on failure or timeout
                    _panic_or_proceed(done, inflight, step)
                    # don't keep futures around in memory longer than needed
                    del futures_, done, inflight

                    # combine pending writes from all tasks
                    pending_writes: deque[tuple[str, Any]] = deque()
                    for task in next_tasks:
                        pending_writes.extend(task.writes)

                    if kwargs['debug']:
                        print_step_writes(step, pending_writes, self.stream_channels_list)

                    # apply writes to channels
                    _apply_writes(
                        checkpoint,
                        channels,
                        pending_writes,
                        self._get_next_version
                    )

                    if 'values' in stream_modes:
                        for chunk in _with_mode(
                            'values',
                            isinstance(kwargs['stream_mode'], list),
                            map_output_values(kwargs['output_keys'], pending_writes, channels)
                        ):
                            yield chunk

                    async for chunk in aput_checkpoint({
                        'source': 'loop',
                        'step': step,
                        'writes': (  # type: ignore
                            _single(map_output_updates(kwargs['output_keys'], next_tasks))
                            if self.stream_mode == 'updates'
                            else _single(map_output_values(kwargs['output_keys'], pending_writes, channels))
                        )
                    }):
                        yield chunk

                    # after execution, check if we should interrupt
                    if _should_interrupt(
                        checkpoint,
                        kwargs.interrupt_after,  # type: ignore
                        self.stream_channels_list,
                        next_tasks
                    ):
                        break
                else:
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
            await asyncio.shield(asyncio.gather(*background_tasks))

    def _set_defaults(self, **data: Unpack[FlowOptions]) -> None:
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

def _with_mode(mode: StreamMode, on: bool, iterator: Iterator[Any]) -> Iterator[Any]:
    if on:
        for chunk in iterator:
            yield mode, chunk
    else:
        yield from iterator

def _increment(current: Optional[int]) -> int:
    return current + 1 if current is not None else 1

def _single[T](iterator: Iterator[T]) -> Optional[T]:
    for item in iterator:
        return item

def _apply_writes(
    checkpoint: Checkpoint,
    channels: dict[str, Channel],
    pending_writes: Sequence[tuple[str, Any]],
    get_next_version: Optional[Callable[[int, Channel], int]]
) -> None:
    pending_writes_by_channel: dict[str, list[Any]] = defaultdict(list)

    for chan, value in pending_writes:
        if chan == TASKS:
            pending_writes_by_channel[PENDING_WRITES_CHANNEL].append(value)
        else:
            pending_writes_by_channel[chan].append(value)

    if checkpoint['channel_versions']:
        max_version = max(checkpoint['channel_versions'].values())
    else:
        max_version = None

    updated_channels: set[str] = set()
    # Apply writes to channels
    for chan, values in pending_writes_by_channel.items():
        if chan in channels:
            try:
                updated = channels[chan].update(values)
            except InvalidUpdateError as e:
                raise InvalidUpdateError(
                    f'Invalid update for channel {chan}: {e}.'
                ) from e
            if updated and get_next_version is not None:
                checkpoint['channel_versions'][chan] = get_next_version(max_version, channels[chan])
            updated_channels.add(chan)
        else:
            logger.warning(f'Skipping write for channel {chan} which has no readers.')
    # Channels that weren't updated in this step are notified of a new step
    for chan in channels:
        if chan not in updated_channels:
            if channels[chan].update([]) and get_next_version is not None:
                checkpoint['channel_versions'][chan] = get_next_version(max_version, channels[chan])

def _local_write(
    commit: Callable[[Sequence[tuple[str, Any]]], None],
    processes: dict[str, PregelNode],
    channels: dict[str, Channel],
    writes: Sequence[tuple[str, Any]]
) -> None:
    for chan, value in writes:
        if chan == TASKS:
            if not isinstance(value, Send):
                raise ValueError(f'Invalid packet type. Expected Send, got {value}.')
            if value.node not in processes:
                raise ValueError(f'Invalid node name {value.node} in packet.')
        elif chan not in channels:
            logger.warning(f'Skipping write for channel {chan}, which has no readers.')
    commit(writes)

def _local_read(
    checkpoint: Checkpoint,
    channels: dict[str, Channel],
    writes: Sequence[tuple[str, Any]],
    select: Union[str, list[str]],
    fresh: bool = False
) -> Union[dict[str, Any], Any]:
    if fresh:
        checkpoint = create_checkpoint(checkpoint, channels, -1)
        with ChannelManager(channels, checkpoint) as channels:
            _apply_writes(copy_checkpoint(checkpoint), channels, writes, None)
            return read_channels(channels, select)
    return read_channels(channels, select)

def _process_input(
    step: int,
    name: str,
    process: PregelNode,
    managed: dict[str, ManagedValueSpec],
    channels: dict[str, Channel]
) -> Iterator[Any]:
    if isinstance(process.channels, dict):
        try:
            value = {
                k: read_channel(channels, chan, catch=chan not in process.triggers)
                for k, chan in process.channels.items()
                if isinstance(chan, str)
            }
            managed_values = {}
            for key, chan in process.channels.items():
                if is_managed_value(chan):
                    managed_values[key] = managed[key](step, PregelTaskDescription(name, value))
            value.update(managed_values)
        except EmptyChannelError:
            return
    elif isinstance(process.channels, list):
        for chan in process.channels:
            try:
                value = read_channel(channels, chan, catch=False)
                break
            except EmptyChannelError:
                pass
        else:
            return
    else:
        raise TypeError(
            f'Invalid channels type for process. Expected dict or list, got {process.channels}.'
        )

    if process.mapper is not None:
        value = process.mapper(value)

    yield value

@overload
def _prepare_next_tasks(
    checkpoint: Checkpoint,
    processes: dict[str, PregelNode],
    channels: dict[str, Channel],
    managed: dict[str, ManagedValueSpec],
    step: int,
    for_execution: Literal[False],
    get_next_version: Literal[None] = None,
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
    get_next_version: Callable[[int, Channel], int],
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
    get_next_version: Union[Callable[[int, Channel], int], None] = None,
    **kwargs
) -> tuple[Checkpoint, Union[list[PregelTaskDescription], list[PregelExecutableTask]]]:
    # Check if any processes should be run in next step
    # If so, prepare the values to be passed to them
    checkpoint = copy_checkpoint(checkpoint)
    tasks: list[Union[PregelTaskDescription, PregelExecutableTask]]

    # Consume pending packets
    for packet in checkpoint['pending_sends']:
        if not isinstance(packet, Send):
            logger.warning(f'Ignoring invalid packet type {type(packet)} in pending sends.')
            continue
        if for_execution:
            if node := processes[packet.node].get_node():
                writes = deque()
                tasks.append(
                    PregelExecutableTask(
                        name=packet.node,
                        data=packet.arg,
                        process=node,
                        writes=writes,
                        triggers=[TASKS],
                        kwargs={
                            **kwargs,
                            WRITE_KEY: partial(
                                _local_write,
                                writes.extend,
                                processes,
                                channels
                            ),
                            READ_KEY: partial(
                                _local_read,
                                checkpoint,
                                channels,
                                tasks
                            )
                        }
                    )
                )
        else:
            tasks.append(PregelTaskDescription(packet.node, packet.arg))

    if for_execution:
        checkpoint['pending_sends'].clear()

    # Collect channels to consume
    channels_to_consume = set()

    # Check if any processes should be run in next step
    # If so, prepare the values to be passed to them
    version_type = type(next(iter(checkpoint['channel_versions'].values()), None))
    null_version = version_type()
    if null_version is None:
        return checkpoint, tasks
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
                and checkpoint['channel_versions'].get(chan, null_version) > seen.get(chan, null_version)
            )
        ]:
            channels_to_consume.update(triggers)
            try:
                value = next(_process_input(step, name, process, managed, channels))
            except StopIteration:
                continue

            # update seen versions
            if for_execution:
                seen.update({
                    chan: checkpoint['channel_versions'][chan]
                    for chan in process.triggers
                    if chan in checkpoint['channel_versions']
                })

            if for_execution:
                if node := process.get_node():
                    writes = deque()
                    triggers = sorted(triggers)
                    tasks.append(
                        PregelExecutableTask(
                            name=name,
                            data=value,
                            process=node,
                            writes=writes,
                            triggers=triggers,
                            kwargs={
                                **kwargs,
                                WRITE_KEY: partial(
                                    _local_write,
                                    writes.extend,
                                    processes,
                                    channels
                                ),
                                READ_KEY: partial(
                                    _local_read,
                                    checkpoint,
                                    channels,
                                    writes
                                )
                            }
                        )
                    )
            else:
                tasks.append(PregelTaskDescription(name, value))

    # Find the highest version of all channels
    if checkpoint['channel_versions']:
        max_version = max(checkpoint['channel_versions'].values())
    else:
        max_version = None
    # Consume all channels that were read
    if for_execution:
        for chan in channels_to_consume:
            if channels[chan].consume():
                checkpoint['channel_versions'][chan] = get_next_version(max_version, channels[chan])

    return checkpoint, tasks