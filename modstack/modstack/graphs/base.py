from abc import ABC, abstractmethod
from enum import Enum
import logging
from typing import Callable, Dict, List, NamedTuple, Optional, TYPE_CHECKING, Type, Union
import uuid

from pydantic import BaseModel, Field

from modstack.utils.string import is_uuid

if TYPE_CHECKING:
    from modstack.modules.base import Module

logger = logging.getLogger(__name__)

class CurveStyle(str, Enum):
    """
    Enum for different curve styles.
    """

    BASIS = "basis"
    BUMP_X = "bumpX"
    BUMP_Y = "bumpY"
    CARDINAL = "cardinal"
    CATMULL_ROM = "catmullRom"
    LINEAR = "linear"
    MONOTONE_X = "monotoneX"
    MONOTONE_Y = "monotoneY"
    NATURAL = "natural"
    STEP = "step"
    STEP_AFTER = "stepAfter"
    STEP_BEFORE = "stepBefore"

class Node(NamedTuple):
    """
    Node in a graph.
    """

    id: str
    data: Union[Type[BaseModel], Module]

class Edge(NamedTuple):
    """
    Edge in a graph.
    """

    source: str
    target: str
    data: Optional[str] = None

class Branch(NamedTuple):
    """
    Branch in a graph.
    """

    condition: Callable[..., str]
    ends: Optional[dict[str, str]]

class Graph(BaseModel):
    """
    Graph of nodes and edges.
    """

    nodes: Dict[str, Node] = Field(default_factory=dict)
    edges: List[Edge] = Field(default_factory=list)

    def __bool__(self):
        return bool(self.nodes)

    def add_node(
        self,
        data: Union[Type[BaseModel], Module],
        id_: Optional[str] = None
    ) -> Node:
        if id_ is not None and self.node_exists(id_):
            raise ValueError(f'Node with id {id_} already exists.')
        node = Node(id_ or self.next_id(), data=data)
        self.nodes[node.id] = node
        return node

    def remove_node(self, id_: str) -> None:
        self.nodes.pop(id_)
        self.edges = [
            edge
            for edge in self.edges
            if edge.source != id_ and edge.target != id_
        ]

    def add_edge(
        self,
        source: str,
        target: str,
        data: Optional[str] = None
    ) -> Edge:
        if not self.node_exists(source):
            raise ValueError(f'Source node with id {source} not in graph.')
        if not self.node_exists(target):
            raise ValueError(f'Target node with id {target} not in graph.')
        edge = Edge(source, target, data=data)
        self.edges.append(edge)
        return edge

    def extend(self, graph: 'Graph') -> tuple[Node | None, Node | None]:
        if all(is_uuid(node.id) for node in graph.nodes.values()):
            prefix = ''
        def prefixed(id_: str) -> str:
            return f'{prefix}:{id_}' if prefix else id_

        self.nodes.update({prefixed(k): Node(prefixed(k), v.data) for k, v in graph.nodes.items()})
        self.edges.extend([
            Edge(prefixed(edge.source), prefixed(edge.target), edge.data)
            for edge in graph.edges
        ])

        first, last = graph.first_node(), graph.last_node()
        return (
            Node(prefixed(first.id), first.data) if first else None,
            Node(prefixed(last.id), last.data) if last else None
        )

    def first_node(self) -> Optional[Node]:
        targets = {edge.target for edge in self.edges}
        found = []
        for node in self.nodes.values():
            if node.id not in targets:
                found.append(node)
        return found[0] if len(found) == 1 else None

    def last_node(self) -> Optional[Node]:
        sources = {edge.source for edge in self.edges}
        found = []
        for node in self.nodes.values():
            if node.id not in sources:
                found.append(node)
        return found[0] if len(found) == 1 else None

    def node_exists(self, id_: str) -> bool:
        return id_ in self.nodes

    def edge_exists(self, source: str, target: str) -> bool:
        return len(filter(
            lambda edge: edge.source == source and edge.target == target,
            self.edges
        )) > 0

    def next_id(self) -> str:
        return uuid.uuid4().hex

class AsGraph(ABC):
    """
    Interface for getting the Graph representation of the implementing type.
    """

    @abstractmethod
    def as_graph(self, **kwargs) -> Graph:
        """
        Get the Graph representation of this type.
        """