from collections import deque
from typing import Any, NamedTuple, Union

from modstack.modules import Module

class GraphNode:
    pass

class GraphEdge:
    pass

class GraphBranch:
    pass

class PipelineTaskDescription(NamedTuple):
    name: str
    data: Any

class PipelineExecutableTask(NamedTuple):
    name: str
    data: Any
    process: Module
    writes: deque[tuple[str, Any]]

class StateSnapshot(NamedTuple):
    values: Union[Any, dict[str, Any]]
    next: tuple[str, ...]