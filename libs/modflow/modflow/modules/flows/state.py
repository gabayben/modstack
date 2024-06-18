"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/graphs/state.py
"""
from functools import partial
import inspect
import logging
from typing import Any, Optional, Sequence, Type, Union, get_origin, get_type_hints, override

from pydantic import BaseModel

from modflow import All
from modflow.channels import BinaryOperatorAggregate, Channel, DynamicBarrierValue, EphemeralValue, LastValue, NamedBarrierValue, WaitForNames
from modflow.checkpoints import Checkpointer
from modflow.constants import END, HIDDEN, ROOT_KEY, START
from modflow.managed import ManagedValue, is_managed_value
from modflow.modules import Branch, ChannelRead, ChannelWrite, ChannelWriteEntry, CompiledFlow, Flow, PregelNode
from modflow.modules.write import SKIP_WRITE
from modstack.modules import Functional, Module
from modstack.utils.serialization import create_schema

logger = logging.getLogger(__name__)

class StateFlow(Flow):
    channels: dict[str, Channel]
    managed_values: dict[str, Type[ManagedValue]]

    @override
    @property
    def _all_edges(self) -> set[tuple[str, str]]:
        return self.edges | {
            (source, end)
            for sources, end in self.waiting_edges
            for source in sources
        }

    def __init__(self, schema: Type):
        super().__init__()
        self.schema = schema
        self.channels, self.managed_values = _get_channels(schema)
        if any(isinstance(c, BinaryOperatorAggregate) for c in self.channels.values()):
            self._supports_multiple_edges = True
        self.waiting_edges: set[tuple[tuple[str, ...], str]] = set()

    @override
    def add_edge(
        self,
        source: Union[str, list[str]],
        target: str
    ) -> None:
        if isinstance(source, str):
            return super().add_edge(source, target)

        if self.compiled:
            logger.warning(
                'Adding an edge to a flow that had already been compiled. '
                'This will not be reflected in the compiled flow.'
            )
        for node in source:
            if node == END:
                raise ValueError(f'{END} cannot be a source node.')
            if node not in self.nodes:
                raise ValueError(f'Need to add {node} with `add_node` first.')
        if target == START:
            raise ValueError(f'{START} cannot be a target node.')
        if target not in self.nodes:
            raise ValueError(f'Need to add {target} with `add_node` first.')

        self.waiting_edges.add((tuple(source), target))

    @override
    def compile(
        self,
        checkpointer: Optional[Checkpointer] = None,
        interrupt_before: Optional[Union[All, Sequence[str]]] = None,
        interrupt_after: Optional[Union[All, Sequence[str]]] = None,
        debug: bool = False
    ) -> 'CompiledStateFlow':
        interrupt_before = interrupt_before or []
        interrupt_before = interrupt_after or []

        self.validate(
            (interrupt_before if interrupt_before != '*' else [])
            + interrupt_after if interrupt_after != '*' else [] #type: ignore
        )
        self._compiled = True

        state_keys = list(self.channels)
        output_channels = state_keys[0] if state_keys == [ROOT_KEY] else state_keys
        compiled_flow = CompiledStateFlow(
            builder=self,
            nodes={},
            channels={**self.channels, START: EphemeralValue(self.schema)}, #type: ignore[call-args]
            input_channels=START,
            output_channels=output_channels,
            stream_channels=output_channels,
            interrupt_before=interrupt_before,
            interrupt_after=interrupt_after,
            stream_mode='updates',
            auto_validate=False,
            debug=debug
        )

        compiled_flow.attach_node(START, None)
        for name, node in self.nodes.items():
            compiled_flow.attach_node(name, node)
        for source, target in self.edges:
            compiled_flow.attach_edge(source, target)
        for sources, target in self.waiting_edges:
            compiled_flow.attach_edge(sources, target)
        for source, branches in self.branches.items():
            for name, branch in branches.items():
                compiled_flow.attach_branch(source, name, branch)

        compiled_flow.validate_flow()
        return compiled_flow

class CompiledStateFlow(CompiledFlow):
    builder: StateFlow

    @override
    @property
    def input_schema(self) -> Type[BaseModel]:
        return create_schema(
            self.get_name(suffix='Input'),
            self.builder.schema #type: ignore
        )

    @override
    @property
    def output_schema(self) -> Type[BaseModel]:
        return create_schema(
            self.get_name(suffix='Output'),
            self.builder.schema #type: ignore
        )

    @override
    def attach_node(self, name: str, node: Optional[Module]) -> None:
        state_keys = list(self.builder.channels)

        def get_state_key(input_: Optional[dict], key: str, **kwargs) -> Any:
            if input_ is None:
                return SKIP_WRITE
            if not isinstance(input_, dict):
                raise ValueError(f'Expected a dict, got {input_}.')
            return input_.get(key, SKIP_WRITE)

        # state updaters
        state_write_entries = (
            [ChannelWriteEntry(ROOT_KEY, skip_none=True)]
            if state_keys == [ROOT_KEY]
            else [
                ChannelWriteEntry(
                    key,
                    mapper=Functional(get_state_key, name=key)
                )
                for key in state_keys
            ]
        )

        # add node and output channel
        if name == START:
            self.nodes[START] = PregelNode(
                channels=[START],
                triggers=[START],
                writers=[ChannelWrite(state_write_entries, [HIDDEN])],
                tags=[HIDDEN]
            )
        else:
            self.nodes[name] = PregelNode(
                channels=(
                    state_keys
                    if state_keys == [ROOT_KEY]
                    else {chan: chan for chan in state_keys} | self.builder.managed_values
                ),
                triggers=[],
                writers=[
                    ChannelWrite(
                        [ChannelWriteEntry(name, name)] + state_write_entries
                    )
                ],
                mapper=(
                    partial(_coerce_state, self.builder.schema)
                    if state_keys != [ROOT_KEY]
                    else None
                )
            ) | node
            self.channels[name] = EphemeralValue(Any, guard=False)

    @override
    def attach_edge(
        self,
        sources: Union[str, Sequence[str]],
        target: str
    ) -> None:
        if isinstance(sources, str):
            if sources == START:
                channel_name = f'start:{target}'
                # register channel
                self.channels[channel_name] = EphemeralValue(Any)
                # subscribe to channel
                self.nodes[target].triggers.append(channel_name)
                # publish to channel
                self.nodes[START] |= ChannelWrite(
                    [ChannelWriteEntry(channel_name, START)],
                    tags=[HIDDEN]
                )
            elif target != END:
                self.nodes[target].triggers.append(sources)
        elif target != END:
            channel_name = f'join:{'+'.join(sources)}:{target}'
            # register channel
            self.channels[channel_name] = NamedBarrierValue(str, set(sources))
            # subscribe to channel
            self.nodes[target].triggers.append(channel_name)
            # publish to channel
            for source in sources:
                self.nodes[source] |= ChannelWrite(
                    [ChannelWriteEntry(channel_name, source)],
                    tags=[HIDDEN]
                )

    @override
    def attach_branch(
        self,
        source: str,
        name: str,
        branch: Branch
    ) -> None:
        def branch_writer(targets: list[str]) -> Optional[ChannelWrite]:
            if filtered_targets := [target for target in targets if target != END]:
                writes = [
                    ChannelWriteEntry(Branch.key(source, name, target), source)
                    for target in filtered_targets
                ]
                if branch.then and branch.then != END:
                    writes.append(
                        ChannelWriteEntry(
                            Branch.key(source, name, 'then'),
                            WaitForNames(set(filtered_targets))
                        )
                    )
                return ChannelWrite(writes, tags=[HIDDEN])
            return None

        # attach branch writer
        self.nodes[source] |= branch.run(branch_writer, _get_state_reader(self.builder)) #type: ignore

        # attach branch subscribers
        targets = (
            branch.path_map.values()
            if branch.path_map
            else [node for node in self.builder.nodes if node != branch.then]
        )
        for target in targets:
            if target != END:
                channel_name = Branch.key(source, name, target)
                self.channels[channel_name] = EphemeralValue(Any)
                self.nodes[target].triggers.append(channel_name)

        # attach then subscriber
        if branch.then and branch.then != END:
            channel_name = Branch.key(source, name, 'then')
            self.channels[channel_name] = DynamicBarrierValue(str)
            self.nodes[branch.then].triggers.append(channel_name)
            for target in targets:
                if target != END:
                    self.nodes[target] |= ChannelWrite(
                        [ChannelWriteEntry(channel_name, target)],
                        tags=[HIDDEN]
                    )

def _get_channels(schema: Type) -> tuple[dict[str, Channel], dict[str, Type[ManagedValue]]]:
    if not hasattr(schema, '__annotations__'):
        return {ROOT_KEY: _get_channel(schema, allow_managed=False)}, {}

    all_values = {
        name: _get_channel(type_)
        for name, type_ in get_type_hints(schema, include_extras=True).items()
        if name != '__slots__'
    }

    # noinspection PyTypeChecker
    return (
        {k: v for k, v in all_values.items() if not is_managed_value(v)},
        {k: v for k, v in all_values.items() if is_managed_value(v)}
    )

def _get_channel(type_: Type, allow_managed: bool = True) -> Union[Channel, Type[ManagedValue]]:
    if managed_value := _is_field_managed_value(type_):
        if allow_managed:
            return managed_value
        raise ValueError(f'{type_} not allowed in this position.')

    if channel := _is_field_binary_op(type_):
        return channel

    return LastValue(type_) #type: ignore[call-args]

def _is_field_binary_op(type_: Type) -> Optional[BinaryOperatorAggregate]:
    if hasattr(type_, '__metadata__'):
        metadata = type_.__metadata__
        if len(metadata) == 1 and callable(metadata[0]):
            signature = inspect.signature(metadata[0])
            params = list(signature.parameters.values())
            if (
                len(params) == 2
                and len([
                    p
                    for p in params
                    if p in [p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD]
                ])
            ):
                return BinaryOperatorAggregate(type_, metadata[0]) #type: ignore[call-args]
    return None

def _is_field_managed_value(type_: Type) -> Optional[Type[ManagedValue]]:
    if hasattr(type_, '__metadata__'):
        metadata = type_.__metadata__
        if len(metadata) == 1:
            decoration = get_origin(metadata[0]) or metadata[0]
            if is_managed_value(decoration):
                return decoration #type: ignore
    return None

def _coerce_state(schema: Type, input_: dict[str, Any]) -> dict[str, Any]:
    return schema(**input_)

def _get_state_reader(builder: StateFlow) -> ChannelRead:
    state_keys = list(builder.channels)
    return partial(
        ChannelRead.do_read,
        channels=state_keys[0] if state_keys == [ROOT_KEY] else state_keys,
        fresh=True,
        mapper=partial(_coerce_state, builder.schema) if state_keys != [ROOT_KEY] else None
    )