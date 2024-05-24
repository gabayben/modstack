"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/graphs/graph.py
"""

from collections import defaultdict
import logging
from typing import Any, Literal, NamedTuple, Optional, Sequence, Union, cast, get_args, get_origin, get_type_hints

from modflow import All
from modflow.channels import EphemeralValue
from modflow.checkpoints import Checkpointer
from modflow.constants import END, START, HIDDEN
from modflow.modules import ChannelWrite, ChannelWriteEntry, Pregel, PregelNode
from modflow.utils.channel_helper import ChannelHelper
from modstack.graphs import Graph
from modstack.modules import Functional, Module, ModuleFunction, ModuleLike, coerce_to_module

logger = logging.getLogger(__name__)

class Branch(NamedTuple):
    path: Module[Any, Union[str, list[str]]]
    path_map: Optional[dict[str, str]] = None
    then: Optional[str] = None

    def run(
        self,
        writer: ModuleFunction[[list[str]], Optional[Module]],
        reader: Optional[ModuleFunction[[dict[str, Any]], Any]] = None
    ) -> Module:
        def route(data: Any, **kwargs) -> Module:
            return self._route(data, writer, reader, **kwargs)
        return ChannelWrite.register_writer(Functional(route))

    def _route(
        self,
        data: Any,
        writer: ModuleFunction[[list[str]], Optional[Module]],
        reader: Optional[ModuleFunction[[...], Any]],
        **kwargs
    ) -> Module:
        result = self.path.invoke(reader(**kwargs) if reader else data)
        if not isinstance(result, list):
            result = [result]
        if self.path_map:
            destinations = [self.path_map[r] for r in result]
        else:
            destinations = result
        if any(dest is None for dest in destinations):
            raise ValueError('Branch did not return a valid destination.')
        return writer(destinations) or data

    @staticmethod
    def key(source: str, branch_name: str, end: str) -> str:
        return f'branch:{source}:{branch_name}:{end}'

class Flow:
    @property
    def compiled(self) -> bool:
        return self._compiled

    @property
    def supports_multiple_edges(self) -> bool:
        return False

    @property
    def _all_edges(self) -> set[tuple[str, str]]:
        return self.edges

    def __init__(self):
        self.nodes: dict[str, Module] = {}
        self.edges: set[tuple[str, str]] = set()
        self.branches: dict[str, dict[str, Branch]] = defaultdict(dict)
        self._compiled: bool = False

    def add_node(
        self,
        node: ModuleLike,
        name: Optional[str] = None
    ) -> None:
        if self.compiled:
            logger.warning(
                'Adding a node to a flow that had already been compiled. '
                'This will not be reflected in the compiled flow.'
            )
        node = coerce_to_module(node)
        name = name or node.get_name()
        if name in self.nodes:
            raise ValueError(f'Node `{name}` is already present.')
        if name == START or name == END:
            raise ValueError(f'Node `{name}` is reserved.')
        self.nodes[name] = node

    def add_edge(self, source: str, target: str) -> None:
        if self.compiled:
            logger.warning(
                'Adding an edge to a flow that had already been compiled. '
                'This will not be reflected in the compiled flow.'
            )
        if source == END:
            raise ValueError(f'{END} cannot be a source node.')
        if target == START:
            raise ValueError(f'{START} cannot be a target node.')
        if not self.supports_multiple_edges and source in set(s for s, _ in self.edges):
            raise ValueError(
                f'Already found path for node {source}.\n'
                f'For multiple edges, use StateGraph with an annotated key.'
            )
        self.edges.add((source, target))

    def add_conditional_edges(
        self,
        source: str,
        path: ModuleLike[Any, Union[str, list[str]]],
        path_map: Optional[Union[dict[str, str], list[str]]] = None,
        then: Optional[str] = None,
        name: Optional[str] = None
    ) -> None:
        if self.compiled:
            logger.warning(
                'Adding an edge to a flow that had already been compiled. '
                'This will not be reflected in the compiled flow.'
            )
        if isinstance(path_map, dict):
            pass
        elif isinstance(path_map, list):
            path_map = {name: name for name in path_map}
        elif return_type := get_type_hints(path).get('return'):
            if get_origin(return_type) == Literal:
                path_map = {name: name for name in get_args(return_type)}
        path = coerce_to_module(path)
        name = name or path.get_name() or 'condition'
        if name in self.branches[source]:
            raise ValueError(f'Branch with name {name} already exists for node {source}')
        self.branches[source][name] = Branch(path, path_map, then=then)

    def set_entry_point(self, key: str) -> None:
        self.add_edge(START, key)

    def set_conditional_entry_poiny(
        self,
        path: ModuleLike[Any, Union[str, list[str]]],
        path_map: Optional[Union[dict[str, str], list[str]]] = None,
        then: Optional[str] = None,
        name: Optional[str] = None
    ) -> None:
        self.add_conditional_edges(
            START,
            path,
            path_map=path_map,
            then=then,
            name=name
        )

    def set_finish_point(self, key: str) -> None:
        self.add_edge(key, END)

    def validate(self, interrupt: Optional[Sequence[str]] = None) -> None:
        # assemble sources
        all_sources = {src for src, _ in self._all_edges}
        for start, branches in self.branches.items():
            all_sources.add(start)
            for cond, branch in branches.items():
                if branch.then is not None:
                    if branch.path_map is not None:
                        for end in branch.path_map.values():
                            if end != END:
                                all_sources.add(end)
                    else:
                        for node in self.nodes:
                            if node != start and node != branch.then:
                                all_sources.add(node)

        # validate sources
        for node in self.nodes:
            if node not in all_sources:
                raise ValueError(f'Node {node} is a dead end.')
        for source in all_sources:
            if source not in self.nodes and source != START:
                raise ValueError(f'Found edge starting at unknown node {source}.')

        # assemble targets
        all_targets = {target for _, target in self._all_edges}
        for start, branches in self.branches.items():
            for cond, branch in branches.items():
                if branch.then is not None:
                    all_targets.add(branch.then)
                if branch.path_map is not None:
                    for end in branch.path_map.values():
                        if end not in self.nodes and end != END:
                            raise ValueError(f'{cond} branch found unknown target {end} at {start} node.')

        # validate targets
        for node in self.nodes:
            if node not in all_targets:
                raise ValueError(f'Node {node} not reachable.')
        for target in all_targets:
            if target not in self.nodes and target != END:
                raise ValueError(f'Found edge ending at unknown node {target}.')

        # validate interrupt
        if interrupt:
            for node in interrupt:
                if node not in self.nodes:
                    raise ValueError(f'Unknown interrupt node {node}.')

    def compile(
        self,
        checkpointer: Optional[Checkpointer] = None,
        interrupt_before: Optional[Union[All, Sequence[str]]] = None,
        interrupt_after: Optional[Union[All, Sequence[str]]] = None,
        debug: bool = False
    ) -> 'CompiledFlow':
        interrupt_before = interrupt_before or []
        interrupt_after = interrupt_after or []

        self.validate(
            (interrupt_before if interrupt_before != '*' else []) +
            interrupt_after if interrupt_after != '*' else [] # type: ignore
        )
        self._compiled = True

        compiled_flow = CompiledFlow(
            builder=self,
            nodes={},
            channels={START: EphemeralValue(Any), END: EphemeralValue(Any)},
            input_channels=START,
            output_channels=END,
            stream_channels=[],
            interrupt_before=interrupt_before,
            interrupt_after=interrupt_after,
            checkpointer=checkpointer,
            stream_mode='values',
            auto_validate=False,
            debug=debug
        )

        for name, node in self.nodes.items():
            compiled_flow.attach_node(name, node)
        for source, target in self.edges:
            compiled_flow.attach_edge(source, target)
        for source, branches in self.branches.items():
            for name, branch in branches.items():
                compiled_flow.attach_branch(source, name, branch)

        return compiled_flow

class CompiledFlow(Pregel):
    builder: Flow

    def attach_node(self, name: str, node: Module) -> None:
        self.channels[name] = EphemeralValue(Any)
        self.nodes[name] = (
            PregelNode(channels=[], triggers=[])
            | node
            | ChannelWrite([ChannelWriteEntry(name)], tags=[HIDDEN])
        )
        cast(list[str], self.stream_channels).append(name)

    def attach_edge(self, source: str, target: str) -> None:
        if target == END:
            self.nodes[source].writers.append(
                ChannelWrite([ChannelWriteEntry(END)], tags=[HIDDEN])
            )
        else:
            self.nodes[target].channels.append(source)
            self.nodes[target].triggers.append(source)

    def attach_branch(self, source: str, name: str, branch: Branch) -> None:
        def branch_writer(ends: list[str]) -> ChannelWrite:
            channels = [
                Branch.key(source, name, end)
                if end != END
                else END
                for end in ends
            ]
            return ChannelWrite(
                [ChannelWriteEntry(chan) for chan in channels],
                tags=[HIDDEN]
            )

        # attach hidden start node
        if source == START and START not in self.nodes:
            self.nodes[START] = ChannelHelper.subscribe_to(START, tags=[HIDDEN])

        # attach branch writer
        self.nodes[source] |= branch.run(branch_writer)

        # attach branch readers
        ends = branch.path_map.values() if branch.path_map else [node for node in self.nodes]
        for end in ends:
            if end != END:
                channel_name = Branch.key(source, name, end)
                self.channels[channel_name] = EphemeralValue(Any)
                self.nodes[end].channels.append(channel_name)
                self.nodes[end].triggers.append(channel_name)

    def as_graph(self, **kwargs) -> Graph:
        pass