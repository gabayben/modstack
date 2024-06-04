"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/pregel/debug.py
"""

from collections import defaultdict
from datetime import datetime, timezone
import json
from pprint import pformat
from typing import Any, Iterator, Literal, Mapping, NotRequired, Optional, Sequence, TypedDict, Union
from uuid import UUID, uuid5

from modflow import PregelExecutableTask
from modflow.channels import Channel
from modflow.constants import HIDDEN
from modflow.utils.io import read_channels
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
        if 'tags' in task.kwargs and HIDDEN in task.kwargs['tags']:
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
    timestamp = datetime.now(timezone.utc).isoformat()
    for i, task in enumerate(tasks):
        if 'tags' in task.kwargs and HIDDEN in task.kwargs['tags']:
            continue
        yield TaskResultDebugOutput(
            step=step,
            timestamp=timestamp,
            payload=TaskResultPayload(
                id=str(uuid5(TASK_NAMESPACE, json.dumps((task.name, step, i)))),
                name=task.name,
                result=[w for w in task.writes if w[0] in stream_channels]
            )
        )

def map_debug_checkpoint(
    step: int,
    channels: Mapping[str, Channel],
    stream_channels: Union[str, Sequence[str]],
    **kwargs
) -> CheckpointDebugOutput:
    return CheckpointDebugOutput(
        step=step,
        timestamp=datetime.now(timezone.utc).isoformat(),
        payload=CheckpointPayload(
            values=read_channels(channels, stream_channels),
            config=kwargs
        )
    )

def print_step_tasks(step: int, next_tasks: list[PregelExecutableTask]) -> None:
    n_tasks = len(next_tasks)
    print(
        f'[{step}:tasks] '
        + f"Starting step {step} with {n_tasks} task{'s' if n_tasks > 1 else ''}:\n"
        + "\n".join(
            f"- {name} -> {pformat(val)}"
            for name, val, _, _, _, _ in next_tasks
        )
    )

def print_step_writes(
    step: int, writes: Sequence[tuple[str, Any]], whitelist: Sequence[str]
) -> None:
    by_channel: dict[str, list[Any]] = defaultdict(list)
    for channel, value in writes:
        if channel in whitelist:
            by_channel[channel].append(value)
    print(
        f'[{step}:writes] '
        + f"Finished step {step} with writes to {len(by_channel)} channel{'s' if len(by_channel) > 1 else ''}:\n"
        + "\n".join(
            f"- {name} -> {', '.join(pformat(v) for v in vals)}"
            for name, vals in by_channel.items()
        )
    )

def print_step_checkpoint(
    step: int, channels: Mapping[str, Channel], whitelist: Sequence[str]
) -> None:
    print(
        f'[{step}:checkpoint] '
        + f"State at the end of step {step}:\n"
        + pformat(read_channels(channels, list(whitelist)), depth=3)
    )