"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/pregel/debug.py
"""
from datetime import datetime, timezone
import json
from typing import Any, Iterator, Literal, NotRequired, Optional, Sequence, TypedDict, Union
from uuid import UUID, uuid5

from modflow import PregelExecutableTask
from modflow.constants import TAG_HIDDEN
from modstack.typing import Serializable

class TaskPayload(TypedDict):
    id: str
    name: str
    triggers: list[str]
    data: Any

class TaskResultPayload(TypedDict):
    id: str
    name: str
    result: list[tuple[str, Any]]

class CheckpointPayload(TypedDict):
    values: dict[str, Any]
    config: NotRequired[Optional[dict[str, Any]]]

class DebugOutputBase(Serializable):
    step: int
    type: str
    timestamp: str
    payload: dict[str, Any]

class TaskDebugOutput(DebugOutputBase):
    type: Literal['task'] = 'task'
    payload: TaskPayload

class TaskResultDebugOutput(DebugOutputBase):
    type: Literal['task_result'] = 'task_result'
    payload: TaskResultPayload

class CheckpointDebugOutput(DebugOutputBase):
    type: Literal['checkpoint'] = 'checkpoint'
    payload: CheckpointPayload

DebugOutput = Union[TaskDebugOutput, TaskResultDebugOutput, CheckpointDebugOutput]
TASK_NAMESPACE = UUID('6ba7b831-9dad-11d1-80b4-00c04fd430c8')

def map_debug_tasks(step: int, tasks: list[PregelExecutableTask]) -> Iterator[TaskDebugOutput]:
    timestamp = datetime.now(timezone.utc).isoformat()
    for i, task in enumerate(tasks):
        if 'tags' in task.kwargs and TAG_HIDDEN in task.kwargs['tags']:
            continue
        yield TaskDebugOutput(
            step=step,
            timestamp=timestamp,
            payload=TaskPayload(
                id=str(uuid5(TASK_NAMESPACE, json.dumps((task.name, step, i)))),
                name=task.name,
                triggers=task.triggers,
                data=task.data
            )
        )

def map_debug_task_results(
    step: int,
    tasks: list[PregelExecutableTask],
    stream_channels: Sequence[str]
) -> Iterator[TaskResultDebugOutput]:
    pass