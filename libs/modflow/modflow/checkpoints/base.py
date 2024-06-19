"""
Credit to LangGraph - https://github.com/langchain-ai/langgraph/tree/main/langgraph/checkpoints/base.py
"""

from abc import ABC, abstractmethod
from collections import defaultdict
from enum import StrEnum
from typing import Any, AsyncIterator, Iterator, Literal, NamedTuple, NotRequired, Optional, Protocol, TypedDict

from modflow import Send
from modflow.channels import Channel

class CheckpointMetadata(TypedDict, total=False):
    """
    The source of the checkpoint.
    - "input": The checkpoint was created from an input to execute pregel.
    - "loop": The checkpoint was created from inside the pregel loop.
    - "update": The checkpoint was created from a manual state update.
    """
    source: Literal['input', 'loop', 'update']

    """
    The step number of the checkpoint.
    -1 for the first "input" checkpoint.
    0 for the first "loop" checkpoint.
    n for the nth checkpoint afterwards.
    """
    step: int

    """
    The writes that were made between the previous checkpoint and this one.
    Mapping from node name to writes emitted by that node.
    """
    writes: dict[str, Any]

    """
    The score of the checkpoint.
    The score can be used to mark a checkpoint as "good".
    """
    score: NotRequired[Optional[int]]

class Checkpoint(TypedDict):

    """
    The ID of the checkpoint. This is both unique and monotonically
    increasing, so can be used for sorting checkpoints from first to last.
    """
    id: str

    """
    The version of the checkpoint format. Currently 1.
    """
    version: int

    """
    The timestamp of the checkpoint in ISO 8601 format.
    """
    timestamp: str

    """
    The versions of the channels at the time of the checkpoint.
    The keys are channel names and the values are the logical time step
    at which the channel was last updated.
    """
    channel_versions: defaultdict[str, int]

    """
    Map from node ID to map from channel name to version seen.
    This keeps track of the versions of the channels that each node has seen.
    Used to determine which nodes to execute next.
    """
    versions_seen: defaultdict[str, defaultdict[str, int]]

    """
    The values of the channels at the time of the checkpoint.
    Mapping from channel name to channel snapshot value.
    """
    channel_values: dict[str, Any]

    """
    List of packets sent to nodes but not yet processed.
    Cleared by the next checkpoint.
    """
    pending_sends: list[Send]

class CheckpointAt(StrEnum):
    END_OF_STEP = 'end_of_step'
    END_OF_RUN = 'end_of_run'

class CheckpointSerializer(Protocol):
    def loads(self, bytes_: bytes) -> Any:
        pass

    def dumps(self, data: Any) -> bytes:
        pass

class SavedCheckpoint(NamedTuple):
    checkpoint: Checkpoint
    metadata: CheckpointMetadata
    config: dict[str, Any]

class Checkpointer(ABC):
    at: CheckpointAt = CheckpointAt.END_OF_STEP
    serde: CheckpointSerializer

    @property
    def config(self) -> dict[str, Any]:
        return {}

    def __init__(
        self,
        at: CheckpointAt | None = None,
        serde: CheckpointSerializer | None = None
    ):
        self.at = at or self.at
        self.serde = serde or self.serde

    @abstractmethod
    def search(
        self,
        metadata: CheckpointMetadata,
        *,
        limit: Optional[int] = None,
        **kwargs
    ) -> Iterator[SavedCheckpoint]:
        pass

    @abstractmethod
    async def asearch(
        self,
        metadata: CheckpointMetadata,
        *,
        limit: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[SavedCheckpoint]:
        pass

    @abstractmethod
    def get_list(self, limit: Optional[int] = None, **kwargs) -> Iterator[SavedCheckpoint]:
        pass

    @abstractmethod
    async def aget_list(self, limit: Optional[int] = None, **kwargs) -> AsyncIterator[SavedCheckpoint]:
        pass

    @abstractmethod
    def get(self, **kwargs) -> Optional[SavedCheckpoint]:
        pass

    @abstractmethod
    async def aget(self, **kwargs) -> Optional[SavedCheckpoint]:
        pass

    @abstractmethod
    def put(
        self,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        **kwargs
    ) -> dict[str, Any]:
        pass

    @abstractmethod
    async def aput(
        self,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        **kwargs
    ) -> dict[str, Any]:
        pass

    def get_next_version[V: (int, float, str)](
        self,
        current: Optional[V],
        channel: Channel
    ) -> V:
        """
        Get the next version of a channel. Default is to use int versions, incrementing by 1. If you override, you can use str/int/float versions,
        as long as they are monotonically increasing.
        """
        return current + 1 if current is not None else 1