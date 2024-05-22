from collections import deque
from typing import Any, NamedTuple, Optional, Union

from modflow.checkpoints import CheckpointMetadata
from modstack.modules import Module

class FlowNode:
    pass

class FlowEdge:
    pass

class FlowBranch:
    pass

class PregelTaskDescription(NamedTuple):
    name: str
    data: Any

class PregelExecutableTask(NamedTuple):
    name: str
    data: Any
    process: Module
    writes: deque[tuple[str, Any]]
    triggers: list[str]

class StateSnapshot(NamedTuple):
    values: Union[Any, dict[str, Any]]
    next: tuple[str, ...]
    created_at: Optional[str]
    metadata: Optional[CheckpointMetadata]