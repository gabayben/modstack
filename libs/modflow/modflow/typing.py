from collections import deque
from typing import Any, Literal, NamedTuple, Optional, Sequence, Union

from modflow.checkpoints import CheckpointMetadata
from modstack.core.modules import Module
from modstack.core.typing import Serializable

FlowInput = Union[dict[str, Any], Any]
FlowOutputChunk = Union[dict[str, Any], Any]
FlowOutput = Union[FlowOutputChunk, list[FlowOutputChunk]]
All = Literal['*']
StreamMode = Literal['values', 'updates', 'debug']

class RunFlow(Serializable):
    input: FlowInput
    input_keys: Optional[Union[str, Sequence[str]]] = None
    output_keys: Optional[Union[str, Sequence[str]]] = None
    interrupt_before: Optional[Union[Sequence[str], All]] = None
    interrupt_after: Optional[Union[Sequence[str], All]] = None
    config: dict[str, Any] = {}
    stream_mode: StreamMode = 'values'
    debug: Optional[bool] = None

class PregelTaskDescription(NamedTuple):
    name: str
    data: Any

class PregelExecutableTask(NamedTuple):
    name: str
    data: Any
    process: Module
    writes: deque[tuple[str, Any]]
    triggers: list[str]
    kwargs: dict[str, Any]

class StateSnapshot(NamedTuple):
    values: FlowOutputChunk
    next: tuple[str, ...]
    created_at: Optional[str]
    metadata: Optional[CheckpointMetadata]
    kwargs: dict[str, Any]