from collections import deque
from typing import Any, Literal, NamedTuple, NotRequired, Optional, Sequence, TypedDict, Union

from modflow.checkpoints import CheckpointMetadata
from modstack.modules import Module

FlowInput = Union[dict[str, Any], Any]
FlowOutputChunk = Union[dict[str, Any], Any]
FlowOutput = Union[FlowOutputChunk, list[FlowOutputChunk]]
All = Literal['*']
StreamMode = Literal['values', 'updates', 'debug']

class RunFlow(TypedDict, total=False):
    input_keys: NotRequired[Union[str, Sequence[str]]]
    output_keys: NotRequired[Union[str, Sequence[str]]]
    interrupt_before: NotRequired[Union[Sequence[str], All]]
    interrupt_after: NotRequired[Union[Sequence[str], All]]
    config: NotRequired[dict[str, Any]]
    stream_mode: NotRequired[StreamMode]
    debug: NotRequired[bool]

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